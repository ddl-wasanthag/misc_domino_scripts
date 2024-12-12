import csv
import os
import requests
import json
import argparse
import sys

def get_project_collaborators(domino_url, api_key, project_id):
    """Fetch collaborators for a given Domino project ID."""
    url = f"{domino_url}/v4/projects/{project_id}/collaborators"
    headers = {
        "X-Domino-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"DEBUG: Failed to fetch collaborators for project {project_id}: {response.text}")
        return None
    return response.json()

def main():
    parser = argparse.ArgumentParser(description='Get collaborators for projects listed in a CSV file.')
    parser.add_argument('--domino_url', required=True, help='Domino base URL (e.g. https://your-domino-instance.domino.tech)')
    parser.add_argument('--api_key', required=True, help='Domino API key')
    parser.add_argument('--csv_file', default='projects.csv', help='Path to the CSV file containing project_ids')
    args = parser.parse_args()

    # Check if the CSV file exists
    if not os.path.isfile(args.csv_file):
        print(f"DEBUG: The file {args.csv_file} does not exist.")
        sys.exit(1)

    print(f"DEBUG: Reading project IDs from {args.csv_file}")
    with open(args.csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            project_id = row.get('project_id', '').strip()
            if not project_id:
                print("DEBUG: Empty project_id encountered, skipping.")
                continue

            print(f"DEBUG: Found project_id: {project_id}")

            # Get collaborators for this project
            collaborators = get_project_collaborators(args.domino_url, args.api_key, project_id)
            if collaborators is not None:
                print(f"Collaborators for project {project_id}:")
                for c in collaborators:
                    print(json.dumps(c, indent=2))
                print()  # Blank line for readability

if __name__ == "__main__":
    main()
