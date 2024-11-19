# How to run
# python script.py <username> <domino_url> <github_pat> "<job command>" "<cron schedule>" "<project name>"
# python3 create_gbp_and_schjob.py wasantha_gamage prod-field.cs.domino.tech ghp_xxxxxxxxx scripts/h2o_model_train.py '0 0/30 * * * ?' az_idle_wks

import requests
import json
import sys
import os
import argparse
import logging

# Set up logging to a file
script_name = os.path.splitext(os.path.basename(__file__))[0]
logging.basicConfig(filename=f'{script_name}.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def lookup_user(domino_url, api_key, username):
    url = f"https://{domino_url}/v4/users?userName={username}"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        if user_data:
            logging.info(f"User found: {user_data[0]}")
            return user_data[0]
        else:
            logging.error("User not found.")
            print("User not found.")
            sys.exit(1)
    else:
        logging.error("Failed to fetch user.")
        print("Failed to fetch user.")
        sys.exit(1)

def create_git_provider(domino_url, api_key, user_id, github_pat):
    url = f"https://{domino_url}/v4/accounts/{user_id}/gitcredentials"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "name": "sa-git-creds3",
        "gitServiceProvider": "github",
        "accessType": "token",
        "token": github_pat,
        "type": "TokenGitCredentialDto"
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        git_provider = response.json()
        logging.info(f"GitHub provider created successfully: {git_provider}")
        return git_provider
    else:
        logging.error("Failed to create GitHub provider.")
        print("Failed to create GitHub provider.")
        sys.exit(1)

def create_project(domino_url, api_key, user_id, git_provider_id, project_name):
    url = f"https://{domino_url}/v4/projects"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "name": project_name,
        "description": "Created with API",
        "visibility": "Public",
        "ownerId": user_id,
        "mainRepository": {
            "uri": "https://github.com/ddl-wasanthag/WineQualityWorkshop",
            "defaultRef": {"type": "head"},
            "name": "wine_quality",
            "serviceProvider": "github",
            "credentialId": git_provider_id
        },
        "collaborators": [],
        "tags": {"tagNames": []}
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        project = response.json()
        logging.info(f"Project created successfully: {project}")
        return project
    else:
        logging.error("Failed to create project.")
        print("Failed to create project.")
        sys.exit(1)

def schedule_job(domino_url, api_key, project_id, user_id, job_command, cron_string):
    url = f"https://{domino_url}/v4/projects/{project_id}/scheduledjobs"
    headers = {
        "accept": "application/json",
        "X-Domino-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "title": "Scheduled-job-from-api",
        "command": job_command,
        "schedule": {
            "cronString": cron_string,
            "isCustom": True
        },
        "timezoneId": "UTC",
        "isPaused": False,
        "scheduledByUserId": user_id,
        "allowConcurrentExecution": True,
        "hardwareTierIdentifier": "small-k8s",
        "environmentRevisionSpec": "ActiveRevision",
        "notifyOnCompleteEmailAddresses": [
            "wasantha.gamage@dominodatalab.com"
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        logging.info("Scheduled job created successfully.")
    else:
        logging.error("Failed to create scheduled job.")
        print("Failed to create scheduled job.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Create Git provider, project, and schedule a job in Domino.")
    parser.add_argument("username", help="The username of the user")
    parser.add_argument("domino_url", help="The URL of the Domino instance")
    parser.add_argument("github_pat", help="The GitHub Personal Access Token")
    parser.add_argument("job_command", help="The command to run in the scheduled job")
    parser.add_argument("cron_string", help="The cron string for scheduling the job")
    parser.add_argument("project_name", help="The name of the project")

    args = parser.parse_args()

    api_key = os.getenv("DOMINO_USER_API_KEY")
    if not api_key:
        logging.error("API key not set in environment variables.")
        print("API key not set in environment variables.")
        sys.exit(1)
    
    user = lookup_user(args.domino_url, api_key, args.username)
    user_id = user['id']
    logging.info(f"User ID: {user_id}")

    git_provider = create_git_provider(args.domino_url, api_key, user_id, args.github_pat)
    git_provider_id = git_provider['id']
    logging.info(f"GitHub Provider ID: {git_provider_id}")

    project = create_project(args.domino_url, api_key, user_id, git_provider_id, args.project_name)
    project_id = project['id']
    logging.info(f"Project ID: {project_id}")

    schedule_job(args.domino_url, api_key, project_id, user_id, args.job_command, args.cron_string)

if __name__ == "__main__":
    main()
