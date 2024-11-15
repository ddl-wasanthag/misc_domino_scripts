import requests
import json
import os

url = "https://<domino_url>/api/environments/beta/environments"

api_key = os.environ.get("DOMINO_USER_API_KEY")

# Set headers
headers = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "X-DOMINO-API-KEY": api_key
}

# Load the data from the JSON file
with open('body.json', 'r') as f:
    data = json.load(f)

# Send the POST request
response = requests.post(url, headers=headers, json=data)

# Check the response status code and print the result
if response.status_code == 200:
    print("Successfully created the environment")
else:
    print(f"Failed to create the environment. Error message: {response.content}")
