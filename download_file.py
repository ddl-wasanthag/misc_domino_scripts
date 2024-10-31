import os
import requests
import argparse

def get_project_id(domino_url, api_key, project_name):
    """Get the project ID for a given project name."""
    url = f"{domino_url}/v4/projects?name={project_name}"
    headers = {
        "X-Domino-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        project_info = response.json()
        if project_info:
            return project_info[0]['id']
        else:
            raise Exception(f"No project found with name {project_name}")
    else:
        raise Exception(f"Failed to retrieve project: {response.text}")

def get_commit_id(domino_url, api_key, project_id, file_to_download):
    """Get the commit ID for the file to download."""
    url = f"{domino_url}/v4/projects/{project_id}/commits"
    headers = {
        "X-Domino-Api-Key": api_key,
        "accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        commits = response.json()
        # Check for "Added/Modified" or "Rename" messages that contain the file name
        for commit in commits:
            if f"Added/Modified: {file_to_download}" in commit['name'] or f"Rename" in commit['name'] and file_to_download in commit['name']:
                return commit['id']
        raise Exception(f"Commit for {file_to_download} not found.")
    else:
        raise Exception(f"Failed to retrieve commits: {response.text}")

def download_file(domino_url, api_key, project_id, commit_id, file_to_download, output_path):
    """Download the specified file content."""
    url = f"{domino_url}/api/projects/v1/projects/{project_id}/files/{commit_id}/{file_to_download}/content"
    headers = {
        "X-Domino-Api-Key": api_key,
        "accept": "*/*"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"File downloaded successfully to {output_path}")
    else:
        raise Exception(f"Failed to download file: {response.text}")

def main():
    parser = argparse.ArgumentParser(description="Download a file from a Domino project.")
    parser.add_argument('--domino_url', required=True, help='Domino API URL')
    parser.add_argument('--api_key', required=True, help='Domino API Key')
    parser.add_argument('--project_name', required=True, help='Name of the Domino project')
    parser.add_argument('--file_to_download', required=True, help='Name of the file to download')
    parser.add_argument('--output_path', default='/tmp/downloaded_file.txt', help='Output file path (default: /tmp/downloaded_file.txt)')

    args = parser.parse_args()

    try:
        project_id = get_project_id(args.domino_url, args.api_key, args.project_name)
        commit_id = get_commit_id(args.domino_url, args.api_key, project_id, args.file_to_download)
        download_file(args.domino_url, args.api_key, project_id, commit_id, args.file_to_download, args.output_path)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
