# Execute as following
# python3 copy_project_env_vars.py https:/<Domino url> <API key> <source project id>> <destination project id>
import argparse
import requests
import json

def get_env_vars(domino_url, api_key, project_id):
    """Fetch environment variables from a project"""
    url = f"{domino_url}/v4/projects/{project_id}/environmentVariables"
    headers = {
        "accept": "application/json",
        "X-DOMINO-API-KEY": api_key
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: Failed to fetch environment variables from project {project_id}")
        print(f"Response: {response.text}")
        return []

def set_env_var(domino_url, api_key, project_id, name, value):
    """Set an environment variable for a project"""
    url = f"{domino_url}/v4/projects/{project_id}/environmentVariables"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-DOMINO-API-KEY": api_key
    }
    data = json.dumps({"name": name, "value": value})
    
    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        print(f"Successfully set {name} = {value} for project {project_id}")
    else:
        print(f"Error {response.status_code}: Failed to set environment variable {name} in project {project_id}")
        print(f"Response: {response.text}")

def copy_env_vars(domino_url, api_key, source_project_id, dest_project_id):
    """Copy environment variables from source project to destination project"""
    source_vars = get_env_vars(domino_url, api_key, source_project_id)

    if source_vars:
        for var in source_vars:
            name = var["name"]
            value = var["value"]
            set_env_var(domino_url, api_key, dest_project_id, name, value)
    else:
        print("No environment variables found in source project.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy environment variables from one Domino project to another")
    parser.add_argument("domino_url", help="Domino URL")
    parser.add_argument("api_key", help="Domino API key")
    parser.add_argument("source_project_id", help="Source project ID")
    parser.add_argument("dest_project_id", help="Destination project ID")
    
    args = parser.parse_args()

    # Copy environment variables from source to destination
    copy_env_vars(args.domino_url, args.api_key, args.source_project_id, args.dest_project_id)
