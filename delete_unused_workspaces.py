import re
import json
import requests
import logging

# Configure logging
logging.basicConfig(filename='log_file.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def preprocess_json_content(content):
    # Replace ObjectId("...") with just the hexadecimal string
    content = re.sub(r'ObjectId\("([a-fA-F0-9]+)"\)', r'"\1"', content)
    # Replace ISODate("...") with just the date string
    content = re.sub(r'ISODate\("([^"]+)"\)', r'"\1"', content)
    # Replace NumberLong(...) with the number itself
    content = re.sub(r'NumberLong\((\d+)\)', r'\1', content)
    return content

def delete_workspace(api_key, domino_url, project_id, workspace_id):
    url = f"{domino_url}/v4/workspace/project/{project_id}/workspace/{workspace_id}"
    headers = {
        'accept': 'application/json',
        'X-Domino-Api-Key': api_key
    }

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        logging.info(f"Workspace {workspace_id} deleted successfully from project {project_id}.")
        print(f"Workspace {workspace_id} deleted successfully.")
    except requests.exceptions.HTTPError as err:
        logging.error(f"Error deleting workspace {workspace_id} from project {project_id}: {err}")
        print(f"Error deleting workspace: {err}")

def read_json_and_confirm_deletion(api_key, domino_url, json_file):
    workspaces_to_delete = []

    with open(json_file, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue  # Skip empty lines
            try:
                preprocessed_line = preprocess_json_content(line)
                workspace = json.loads(preprocessed_line)

                workspace_id_str = workspace['_id']
                project_id_str = workspace['projectId']
                workspace_name = workspace['name']
                project_name = workspace['projectName']
                user_name = workspace['fullName']
                
                workspace_id = workspace_id_str
                project_id = project_id_str
                
                if workspace_id and project_id:
                    workspaces_to_delete.append((workspace_id, project_id, workspace_name, project_name, user_name))
                else:
                    logging.error(f"Error parsing ObjectId from {workspace_id_str} or {project_id_str}.")
                    print(f"Error parsing ObjectId from {workspace_id_str} or {project_id_str}.")
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON line: {line}")
                print(f"Invalid JSON line: {line}")

    # List workspaces to be deleted
    print("The following workspaces are going to be deleted:")
    for ws in workspaces_to_delete:
        print(f"Workspace Name: {ws[2]}, Project Name: {ws[3]}, User Name: {ws[4]}")
    
    # Ask for user confirmation
    confirmation = input("Do you want to proceed with the deletion of these workspaces? (yes/no): ").strip().lower()
    if confirmation == 'yes':
        for ws in workspaces_to_delete:
            delete_workspace(api_key, domino_url, ws[1], ws[0])
    else:
        print("Deletion cancelled.")
        logging.info("Deletion cancelled by user.")



# Example usage:
api_key = 'xxxxxxxxxx'
domino_url = 'https://your-domino.domino.tech/'
json_file = 'unused_workspaces.json'

read_json_and_confirm_deletion(api_key, domino_url, json_file)

