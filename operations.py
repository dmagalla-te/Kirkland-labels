
import json 
import os
import csv
from connector import *


def banner():
    with open('banner.txt', 'r') as file:
        banner = file.read()
    print(banner)

def read_files(directory_path:str, label_name:str):
     
     #dict that corelates the label name with the agents that has to be assigned
    label_to_agents = {}

    for filename in os.listdir(directory_path):
        print(f'Reading: {filename}')
        #label = filename.split(".")[0]
        label = label_name

        if filename.endswith('.csv'):
            file_path = os.path.join(directory_path, filename)

            with open(file_path, newline="") as csvfile:
                reader = csv.reader(csvfile)

                for row in reader:
                    if label in label_to_agents:
                        label_to_agents[label].append(row[0])
                    else:
                        label_to_agents[label] = [row[0]]

    return label_to_agents

def agents_to_dict(all_agents:dict):

    agents_name_id = {}

    if "endpointAgents" in all_agents:

        for agent in all_agents["endpointAgents"]:
            if agent['clients']:
                #si el agente está en esa lista entonces sacamos su ID
                username =  agent["clients"][0]['userProfile']['userName']
                extracted_username = username.split('\\')[-1]

                agents_name_id[extracted_username] = agent["agentId"]

            #agents_name_id[agent["agentName"]] = agent["agentId"] #esta linea es para el codigo de ABB

    return agents_name_id

def labels_to_dict(all_labels:dict):
    
    labels_name_id = {}

    if "groups" in all_labels:
        for label in all_labels["groups"]:
            labels_name_id[label["name"]] = label["groupId"]

    return labels_name_id

def add_agents(headers:dict, labels_to_agents:dict , account_group:str= "ProServ Enablement"):
    
    agent = {}

    #We get the aid for the target Account group
    acc_endp = "https://api.thousandeyes.com/v6/account-groups.json"
    _,accounts = get_data(headers=headers, endp_url=acc_endp, params={})

    
    for acc in accounts["accountGroups"]:
        if acc["accountGroupName"] == account_group and acc["organizationName"] == account_group:
            aid = acc["aid"]
    

    #Obtenemos todos los agentes de ese account group para sacar su agentId
    agents_url = "https://api.thousandeyes.com/v6/endpoint-agents.json"
    _, all_agents = get_data(headers, agents_url, params={"aid": aid})


    #Con esto tenemos que hacer un diccionario de {Agent_name:agent_id }
    agents_user_agentid = agents_to_dict(all_agents) # <----- aqui la condicion cambia!!! en vez de regresar nombres:agent_id regresaremos: users:agent_is


    #hacemos lo mismo para los labels
    #ya que tenemos los agent IDs buscamos la info del label
    label_url = "https://api.thousandeyes.com/v6/groups/endpoint-agents.json"
    _,all_labels = get_data(headers, label_url, params={"aid": aid})

    labels_name_id = labels_to_dict(all_labels)


    #iterar en el diccionario de labels_to_agents y armar una lista de agent ids por cada agente
    for label, agents in labels_to_agents.items():
        
        if label in labels_name_id:
            old_agentIds = []

            label_details_url = "https://api.thousandeyes.com/v6/groups/endpoint-agents/%s.json" % (labels_name_id[label])
            _,label_details = get_data(headers=headers, endp_url=label_details_url, params={"aid": aid})

            if len(label_details["groups"][0]["endpointAgents"]) > 0:
                for agent in label_details["groups"][0]["endpointAgents"]:
                    old_agentIds.append({"agentId" :agent["agentId"]})

            new_agentsIds = []

            for agent in agents:

                if agent in agents_user_agentid:
                    new_agentsIds.append({"agentId" :agents_user_agentid[agent]})
                else:
                    print(f'This agent does not exists: {agent} in this account group: {account_group}')
            

            #Juntamos la lista de los viejos con los nuevos
            agents = new_agentsIds +  old_agentIds

            #que se haga update si la lista de endpointAgents está vacia?

            #Ahora si agregamos los agentes a ese label
            payload = json.dumps({
                "name": label,
                "endpointAgents": agents
                })
            
            update_label_url = "https://api.thousandeyes.com/v6/groups/%s/update.json?aid=%s" % (labels_name_id[label], aid)
            status_code,update = post_data(headers,update_label_url,payload)
        
            if status_code != 200:
                print("There was an issue with the agents please verify the list")
            else: 
                print(f"Agents added successfully to: {label}")

        else:
            print(f'This label does not exist in the account group {account_group}: {label}')

    return 0

    
