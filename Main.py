from colorama import Fore, Style, Back
from operations import banner, read_files, add_agents


#############################
#           MAIN
#############################

if __name__ == "__main__":

    try:
        
        banner()

        OAuth = input(f"Please provide your ThousandEyes API {Back.RED}{Style.BRIGHT}OAUTH token{Style.RESET_ALL}: ")

        directory_path = f'./CSV'


        HEADERS = {'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + OAuth}
        
        label_name = input(f"\nPlease provide the name of the label: ")


        #1. Label to agents relation:
        labels_to_agents = read_files(directory_path=directory_path, label_name= label_name)

        #2. Assign labels to agents:
        account_group = ""
        add_agents(headers=HEADERS, labels_to_agents=labels_to_agents)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")






