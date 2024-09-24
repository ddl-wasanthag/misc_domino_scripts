import os
import requests
import logging
import csv
from datetime import datetime

# Read API key from environment variable
api_key = os.getenv("DOMINO_USER_API_KEY")

if not api_key:
    raise ValueError("API key is not set in the environment variable DOMINO_USER_API_KEY")

# Base URL
domino_url = "https://your-domino.cs.domino.tech"

# Headers
headers = {
    "accept": "application/json",
    "X-Domino-Api-Key": api_key
}

def fetch_running_apps():
    url = f"{domino_url}/v4/modelProducts"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logging.debug("Apps fetched successfully")
        apps = response.json()
        running_apps = [app for app in apps if app.get("status") == "Running"]
        return running_apps
    else:
        logging.error(f"Failed to fetch apps: {response.status_code}")
        return []

def write_to_csv(running_apps, output_file):
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["name", "fullName", "userName", "email"])

        for app in running_apps:
            name = app.get("name", "")
            publisher = app.get("publisher", {})
            full_name = publisher.get("fullName", "")
            user_name = publisher.get("userName", "")
            email = publisher.get("email", "")
            writer.writerow([name, full_name, user_name, email])

# Example usage
if __name__ == "__main__":
    logging.basicConfig(filename='model_manage_log.txt', level=logging.DEBUG)
    running_apps = fetch_running_apps()
    if running_apps:
        output_file = 'running_apps.csv'
        write_to_csv(running_apps, output_file)
        print(f"Details of running apps have been written to {output_file}")
    else:
        print("No running apps found.")
