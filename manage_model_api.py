import os
import requests
import logging
import argparse
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

def fetch_projects():
    url = f"{domino_url}/v4/projects"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logging.debug("Projects fetched successfully")
        return response.json()
    else:
        logging.error(f"Failed to fetch projects: {response.status_code}")
        return []

def fetch_models(project_id):
    url = f"{domino_url}/v4/modelManager/getModels?projectId={project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logging.debug(f"Models fetched successfully for project {project_id}")
        return response.json()
    else:
        logging.error(f"Failed to fetch models for project {project_id}: {response.status_code}")
        return []

def stop_model_deployment(model_id, active_model_version_id):
    url = f"{domino_url}/v4/models/{model_id}/{active_model_version_id}/stopModelDeployment"
    response = requests.post(url, headers=headers, data="")
    if response.status_code == 200:
        logging.debug(f"Successfully stopped model deployment for model {model_id} version {active_model_version_id}")
        print(f"Successfully stopped model deployment for model {model_id} version {active_model_version_id}")
    else:
        logging.error(f"Failed to stop model deployment for model {model_id} version {active_model_version_id}: {response.status_code}")
        print(f"Failed to stop model deployment for model {model_id} version {active_model_version_id}")

def start_model_deployment(model_id, active_model_version_id):
    url = f"{domino_url}/v4/models/{model_id}/{active_model_version_id}/startModelDeployment"
    response = requests.post(url, headers=headers, data="")
    if response.status_code == 200:
        logging.debug(f"Successfully started model deployment for model {model_id} version {active_model_version_id}")
        print(f"Successfully started model deployment for model {model_id} version {active_model_version_id}")
    else:
        logging.error(f"Failed to start model deployment for model {model_id} version {active_model_version_id}: {response.status_code}")
        print(f"Failed to start model deployment for model {model_id} version {active_model_version_id}")

def format_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')

def show_models(project_id, project_name):
    models = fetch_models(project_id)
    if models:
        print(f"Models for Project ID: {project_id} and Name: {project_name}")
        for model in models:
            print(f"Model ID: {model['id']}")
            print(f"Name: {model['name']}")
            print(f"Description: {model['description']}")
            print(f"Active Version Number: {model['activeVersionNumber']}")
            print(f"Active Model Version ID: {model['activeModelVersionId']}")
            print(f"Active Version Data Plane ID: {model['activeVersionDataPlaneId']}")
            print(f"Active Version Status: {model['activeVersionStatus']}")
            print(f"Last Modified: {format_timestamp(model['lastModified'])}")
            print(f"Project ID: {model['projectId']}")
            print(f"Project Name: {model['projectName']}")
            print(f"Project Owner Username: {model['projectOwnerUsername']}")
            print(f"Owners: {', '.join([owner['fullName'] for owner in model['owners']])}")
            print(f"Is Async: {model['isAsync']}\n")
    else:
        print(f"No models found or failed to fetch models for project {project_id}.")

def main():
    parser = argparse.ArgumentParser(description="Domino Model Manager Operations")
    parser.add_argument("operation", choices=["show", "start", "stop"], help="Operation to perform: show, start, or stop")
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        filename='model_manage_log.txt',
        filemode='a',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG
    )

    projects = fetch_projects()
    if not projects:
        print("No projects found.")
        return

    for project in projects:
        project_id = project['id']
        project_name = project['name']
        logging.debug(f"Operation: {args.operation}, Project ID: {project_id}, Project Name: {project_name}")
        print(f"Performing operation '{args.operation}' on Project ID: {project_id} and Name: {project_name}")

        if args.operation == "show":
            show_models(project_id, project_name)
        else:
            models = fetch_models(project_id)
            if models:
                for model in models:
                    model_id = model['id']
                    active_model_version_id = model['activeModelVersionId']
                    active_version_status = model['activeVersionStatus']

                    if args.operation == "start":
                        start_model_deployment(model_id, active_model_version_id)
                    elif args.operation == "stop" and active_version_status == "Running":
                        stop_model_deployment(model_id, active_model_version_id)
            else:
                print(f"No models found or failed to fetch models for project {project_id}.")

if __name__ == "__main__":
    main()
