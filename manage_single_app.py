'''
Get the model_product_id from your app url EX: https://<your domino url>/modelproducts/67af64014abf2434ae38859c
python3 manage_app.py --stop <model_product_id>
python3 manage_app.py --start <model_product_id>
'''
import os
import requests
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Read API key from environment variable
api_key = os.getenv("DOMINO_USER_API_KEY")
if not api_key:
    raise ValueError("API key is not set in the environment variable DOMINO_USER_API_KEY")

# Base URL for Domino
domino_url = "https://<your domino url>"

# Headers for the API request
headers = {
    "accept": "application/json",
    "X-Domino-Api-Key": api_key
}

def stop_app(model_product_id):
    """Stops a Domino app given its model_product_id."""
    url = f"{domino_url}/v4/modelProducts/{model_product_id}/stop"
    response = requests.post(url, headers=headers, verify=False)
    if response.status_code == 200:
        logging.info(f"Successfully stopped app with id: {model_product_id}")
        print(f"Successfully stopped app with id: {model_product_id}")
    else:
        logging.error(f"Failed to stop app {model_product_id}: {response.status_code}")
        print(f"Failed to stop app {model_product_id}: {response.status_code}")

def start_app(model_product_id):
    """Starts a Domino app given its model_product_id along with required environment and tier IDs."""
    url = f"{domino_url}/v4/modelProducts/{model_product_id}/start"

    body = {}
    
    response = requests.post(url, json=body, headers=headers, verify=False)
    if response.status_code == 200:
        logging.info(f"Successfully started app with id: {model_product_id}")
        print(f"Successfully started app with id: {model_product_id}")
    else:
        logging.error(f"Failed to start app {model_product_id}: {response.status_code}")
        print(f"Failed to start app {model_product_id}: {response.status_code}")

def main():
    parser = argparse.ArgumentParser(
        description="Manage a Domino app by model_product_id: start or stop the app."
    )
    parser.add_argument("model_product_id", help="The model product ID of the app to manage")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--start", action="store_true", help="Start the app")
    group.add_argument("--stop", action="store_true", help="Stop the app")
    
    
    args = parser.parse_args()

    if args.stop:
        stop_app(args.model_product_id)
    elif args.start:
        start_app(args.model_product_id)

if __name__ == "__main__":
    main()

