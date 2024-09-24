import os
import requests
import json
import logging
from datetime import datetime

# Set up logging
log_file = 'report_logs.log'
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Remove default logging handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Add file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Read API key from environment variable
api_key = os.getenv("DOMINO_USER_API_KEY")

if not api_key:
    raise ValueError("API key is not set in the environment variable DOMINO_USER_API_KEY")

# Base URL
domino_url = "https://domino-dev.xxx.com"

# Headers
headers = {
    "accept": "application/json",
    "X-Domino-Api-Key": api_key
}

def fetch_collaborators(project_id):
    url = f"{domino_url}/v4/projects/{project_id}/collaborators"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logging.debug(f"Collaborators fetched successfully for project {project_id}")
        return response.json()
    else:
        logging.error(f"Failed to fetch collaborators for project {project_id}: {response.status_code}")
        return []

def fetch_datasets(project_id):
    url = f"{domino_url}/v4/datasetrw/datasets-v2?projectIdsToInclude={project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logging.debug(f"Datasets fetched successfully for project {project_id}")
        return response.json()
    else:
        logging.error(f"Failed to fetch datasets for project {project_id}: {response.status_code}")
        return []  # Return an empty list if there's an error

def fetch_dataset_grants(dataset_id):
    url = f"{domino_url}/v4/datasetrw/dataset/{dataset_id}/grants"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logging.debug(f"Dataset grants fetched successfully for dataset {dataset_id}")
        return response.json()
    else:
        logging.error(f"Failed to fetch dataset grants for dataset {dataset_id}: {response.status_code}")
        return []

def format_timestamp(timestamp):
    """ Convert Unix timestamp to human-readable format """
    try:
        return datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "N/A"

def format_report(project_id, collaborators_data, datasets_data):
    report_lines = [f"@@@@@ Processing project: {project_id} @@@@@"]
    report_lines.append("\n**** Project Collaborators are: *****")
    
    for collaborator in collaborators_data:
        if isinstance(collaborator, dict):  # Check if collaborator is a dictionary
            collaborator_info = (
                f"- ID: {collaborator.get('id')}\n"
                f"  Username: {collaborator.get('userName')}\n"
                f"  Full Name: {collaborator.get('fullname')}\n"
                f"  Email: {collaborator.get('email')}"
            )
            report_lines.append(collaborator_info)
        else:
            logging.warning(f"Unexpected data format for collaborator: {collaborator}")

    report_lines.append("\n**** Dataset Users and Organization Collaborators are: *****")
    
    for dataset in datasets_data:
        dataset_rw_dto = dataset.get('datasetRwDto', {})
        dataset_id = dataset_rw_dto.get('id')
        if dataset_id:
            report_lines.append(f"\n- Dataset ID: {dataset_id}")
            report_lines.append(f"  Dataset Name: {dataset_rw_dto.get('name')}")
            report_lines.append(f"  Author: {dataset_rw_dto.get('author')}")
            report_lines.append(f"  Size (Bytes): {dataset_rw_dto.get('sizeInBytes')}")
            report_lines.append(f"  Owner Usernames: {', '.join(dataset_rw_dto.get('ownerUsernames', []))}")
            report_lines.append(f"  Status Last Updated Time: {format_timestamp(dataset_rw_dto.get('statusLastUpdatedTime'))}")
            
            # Fetch dataset grants
            grants_data = fetch_dataset_grants(dataset_id)
            
            if isinstance(grants_data, list):  # Ensure it's a list
                for grant in grants_data:
                    if isinstance(grant, dict):  # Check if grant is a dictionary
                        grant_info = (
                            f"  - ID: {grant.get('targetId')}\n"
                            f"    Name: {grant.get('targetName')}\n"
                            f"    Role: {grant.get('targetRole')}\n"
                            f"    Is Organization: {grant.get('isOrganization')}"
                        )
                        report_lines.append(grant_info)
                    else:
                        logging.warning(f"Unexpected data format for grant: {grant}")
            else:
                logging.warning(f"Unexpected data format for dataset grants: {grants_data}")

    return "\n".join(report_lines)

def generate_report(project_id):
    logging.info(f"Generating report for project {project_id}")
    collaborators_data = fetch_collaborators(project_id)
    datasets_data = fetch_datasets(project_id)
    
    # Log the type and content of datasets_data for debugging
    logging.debug(f"datasets_data type: {type(datasets_data)}")
    logging.debug(f"datasets_data content: {datasets_data}")

    return format_report(project_id, collaborators_data, datasets_data)

# Read project IDs from a text file
with open('project_ids.txt', 'r') as file:
    project_ids = [line.strip() for line in file]

# Generate reports for each project ID
all_reports = []
for project_id in project_ids:
    report = generate_report(project_id)
    all_reports.append(report)

# Write the report to a file and print to standard output
report_file = 'report.txt'
with open(report_file, 'w') as file:
    file.write("\n\n".join(all_reports))

print("\n\n".join(all_reports))
