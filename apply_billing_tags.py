"""
Quick Start Guide for the Billing Tags Script
-----------------------------------------------

1. Set Up Environment:
   - Install dependencies:
       pip install requests - probably not needed in Domino Environments
   - Set your Domino API key as an environment variable:
       export DOMINO_USER_API_KEY=<your_api_key_here> - use DOMINO_USER_API_KEY env var inside Domino
   - Update the script’s DOMINO_URL variable with your Domino instance URL.

2. Usage:
   - Dry-run mode (simulate changes):
       This mode lists all projects for members in the specified organization and shows which billing tag would be applied (if none is set) without making any changes.
       Example:
           python3 billing_tags.py --org all-data-scientists --billing-tag Therapeutic_Area2 --dry-run --log-level DEBUG

   - Apply mode (make changes):
       This mode applies the specified billing tag to projects that don’t already have one.
       Example:
           python3 billing_tags.py --org all-data-scientists --billing-tag Therapeutic_Area2 --apply --log-level INFO

3. Logging:
   - The script outputs logs to both the console and a file named after the script (e.g., billing_tags.log) in the current directory.
   - Use the --log-level option (DEBUG, INFO, etc.) to control the verbosity.

The script will:
   - Fetch organizations, users, and projects from your Domino instance.
   - For each project owned by a member of the specified organization, it checks if a billing tag is already configured.
   - If no billing tag is present, it either logs what would be done (dry-run) or applies the billing tag (apply mode).

Happy tagging!
"""
import os
import requests
import argparse
import logging

# Replace with your actual Domino URL
DOMINO_URL = "https://your-domino"

# Get the API key from the environment variable
API_KEY = os.environ.get("DOMINO_USER_API_KEY")

# Set headers for authentication and content type
HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "X-DOMINO-API-KEY": API_KEY
}

def get_organizations():
    url = f"{DOMINO_URL}/api/organizations/v1/organizations/all"
    logging.debug(f"Fetching organizations from URL: {url}")
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    orgs = data.get("orgs", [])
    logging.debug(f"Received {len(orgs)} organizations.")
    return orgs

def get_users():
    url = f"{DOMINO_URL}/api/users/v1/users"
    logging.debug(f"Fetching users from URL: {url}")
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    users = data.get("users", [])
    logging.debug(f"Received {len(users)} users.")
    return users

def get_projects_by_owner(owner_id):
    url = f"{DOMINO_URL}/v4/projects?ownerId={owner_id}"
    logging.debug(f"Fetching projects for owner {owner_id} from URL: {url}")
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    projects_data = response.json()
    if isinstance(projects_data, dict) and "projects" in projects_data:
        project_list = projects_data["projects"]
    elif isinstance(projects_data, list):
        project_list = projects_data
    else:
        project_list = []
    logging.debug(f"Found {len(project_list)} projects for owner {owner_id}.")
    return project_list

def get_billing_tag(project_id):
    url = f"{DOMINO_URL}/v4/projects/{project_id}/billingtag"
    logging.debug(f"Fetching billing tag for project {project_id} from URL: {url}")
    response = requests.get(url, headers=HEADERS)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Error fetching billing tag for project {project_id}: {e}")
        raise

    try:
        data = response.json()
    except ValueError:
        logging.debug(f"No JSON response for billing tag for project {project_id}.")
        return None

    tag = data.get("tag") if data and isinstance(data, dict) else None
    logging.debug(f"Billing tag for project {project_id}: {tag}")
    return tag

def assign_billing_tag(project_id, tag):
    url = f"{DOMINO_URL}/v4/projects/{project_id}/billingtag"
    payload = {"tag": tag}
    logging.debug(f"Assigning billing tag '{tag}' to project {project_id} via URL: {url} with payload: {payload}")
    response = requests.post(url, json=payload, headers=HEADERS)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Error assigning billing tag to project {project_id}: {e}")
        raise
    data = response.json()
    logging.debug(f"Billing tag assignment response for project {project_id}: {data}")
    return data

def main():
    parser = argparse.ArgumentParser(
        description="Assign billing tags to all projects in an organization (if not already configured)."
    )
    parser.add_argument("--org", required=True, help="Organization name (e.g., 'nyc-data-scientists').")
    parser.add_argument("--billing-tag", required=True, help="Billing tag to assign (e.g., 'data_science_org').")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level (default: INFO)."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Show what changes would be applied without making any changes.")
    group.add_argument("--apply", action="store_true", help="Actually apply the billing tag to projects.")
    args = parser.parse_args()

    # Configure logging for both console and file output
    numeric_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(numeric_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler - log filename based on script name (e.g., billing_tags.log)
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    log_filename = f"{script_name}.log"
    fh = logging.FileHandler(log_filename)
    fh.setLevel(numeric_level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    org_name = args.org.strip()
    billing_tag_to_assign = args.billing_tag.strip()

    logging.info(f"Processing organization: {org_name} with billing tag: {billing_tag_to_assign}")

    organizations = get_organizations()
    organization = next((org for org in organizations if org.get("name") == org_name), None)
    if not organization:
        logging.error(f"Organization '{org_name}' not found.")
        return

    logging.info(f"Found organization: {organization.get('name')}")
    member_ids = [member.get("userId") for member in organization.get("members", [])]
    logging.debug(f"Organization members: {member_ids}")

    users = get_users()
    user_dict = {user.get("id"): user for user in users}
    logging.info("Processing members and their projects:")

    for uid in member_ids:
        user = user_dict.get(uid)
        if user:
            full_name = user.get('fullName') or user.get('userName') or uid
            logging.info(f"Member: {full_name} (ID: {uid}, Email: {user.get('email')})")
        else:
            full_name = uid
            logging.info(f"Member: {uid} (user details not found)")

        try:
            project_list = get_projects_by_owner(uid)
        except Exception as e:
            logging.error(f"Failed to fetch projects for member {uid}: {e}")
            continue

        if project_list:
            logging.info(f"Found {len(project_list)} project(s) for member {uid}.")
            for proj in project_list:
                proj_name = proj.get('name', 'Unnamed Project')
                proj_id = proj.get('id', 'No ID')
                logging.info(f"  - Project: {proj_name} (ID: {proj_id})")

                try:
                    current_tag = get_billing_tag(proj_id)
                except Exception as e:
                    logging.error(f"Failed to fetch billing tag for project {proj_id}: {e}")
                    continue

                if current_tag:
                    logging.info(f"       Project already has the billing tag: {current_tag}")
                else:
                    if args.apply:
                        try:
                            assign_billing_tag(proj_id, billing_tag_to_assign)
                            logging.info(f"       Billing tag assigned: {billing_tag_to_assign}")
                        except Exception as e:
                            logging.error(f"Failed to assign billing tag for project {proj_id}: {e}")
                    else:
                        logging.info(f"       [DRY-RUN] Would assign billing tag: {billing_tag_to_assign}")
        else:
            logging.info("  No projects found for this member.")
        logging.debug("-" * 40)

if __name__ == '__main__':
    main()
