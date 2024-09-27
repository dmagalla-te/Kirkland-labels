import httpx
import time
import logging
import logging.handlers
from datetime import datetime


# HTTPX client setup
limits = httpx.Limits(max_keepalive_connections=350, max_connections=777)
timeout = httpx.Timeout(11.0, read=None)
super_http = httpx.Client(limits=limits, timeout=timeout)

# Instantiate httpx.AsyncClient
client = httpx.AsyncClient(limits=limits, timeout=timeout)


def handle_api_errors(response, endpoint):
    """Handle specific API error responses."""
    
    if response.status_code in {400, 401, 403, 404, 405}:
        
        error_message = f"Error {response.status_code} for {endpoint}: {response.text}"
        logging.error(error_message)
        
        return response.status_code, response.json(), True
    
    return None, None, False


def request_with_retry(method, url, **kwargs):

    """Generic request function with retry for rate limiting, timing, extra sleep time, and error handling."""
    start = time.time()
    response = super_http.request(method, url, **kwargs)
    roundtrip = time.time() - start
    
    if response.status_code == 429:
        
        reset_timestamp = int(response.headers.get('x-organization-rate-limit-reset', 0))
        sleep_time = (datetime.fromtimestamp(reset_timestamp) - datetime.now()).total_seconds() + 1
        time.sleep(max(0, sleep_time))
        retry_start = time.time()
        response = super_http.request(method, url, **kwargs)
        roundtrip = time.time() - retry_start
    
    # Handle specific error codes
    status_code, error_response, has_error = handle_api_errors(response, url)
    
    if has_error:

        return status_code, error_response
    
    return response.status_code, response.json()


def get_data(headers, endp_url, params):
    
    status_code, response = request_with_retry('GET', endp_url, headers=headers, params=params)
    
    if isinstance(response, dict) or status_code in {200, 201}:
    
        return status_code, response
    
    else:
        # Handle non-JSON responses or unexpected outcomes
    
        return status_code, {"error": "Unexpected error occurred"}


def post_data(headers, endp_url, payload):
    
    status_code, response = request_with_retry('POST', endp_url, headers=headers, data=payload)
    
    if isinstance(response, dict) or status_code in {200, 201}:
    
        return status_code, response
    
    else:
    
        # Handle non-JSON responses or unexpected outcomes
        return status_code, {"error": "Unexpected error occurred"}
    