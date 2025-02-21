import requests
import json
import os
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Launch inventory jobs for Domino compute environments.")
parser.add_argument("--restrict", type=int, default=None, help="Number of jobs to launch (default: all environments).")
args = parser.parse_args()
job_limit = args.restrict  # Max number of jobs to launch

# Domino API details
DOMINO_URL = os.getenv("DOMINO_URL")
DOMINO_USER_API_KEY = os.getenv("DOMINO_USER_API_KEY")
DOMINO_PROJECT_ID = os.getenv("DOMINO_PROJECT_ID")  # Read project ID from env variable

if not DOMINO_URL or not DOMINO_USER_API_KEY or not DOMINO_PROJECT_ID:
    print("❌ Missing required environment variables: DOMINO_URL, DOMINO_USER_API_KEY, DOMINO_PROJECT_ID")
    exit(1)

# API Headers
HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "X-Domino-Api-Key": DOMINO_USER_API_KEY
}

# Get all compute environments
ENVIRONMENTS_URL = f"{DOMINO_URL}/v4/environments/self"
response = requests.get(ENVIRONMENTS_URL, headers=HEADERS)

if response.status_code != 200:
    print(f"❌ Error fetching environments: {response.text}")
    exit(1)

environments = response.json()

# Extract required fields with error handling
filtered_envs = []
for env in environments:
    filtered_envs.append({
        "id": env["id"],
        "description": env.get("description", ""),
        "name": env["name"],
        "archived": env["archived"],
        "visibility": env["visibility"],
        "owner": env.get("owner", {}).get("username", "Unknown")  # Handle missing owner
    })

# Apply restriction on number of jobs to launch
if job_limit:
    filtered_envs = filtered_envs[:job_limit]

print(f"🚀 Launching {len(filtered_envs)} jobs for inventory collection...")

# Start a job for each environment
JOB_URL = f"{DOMINO_URL}/v4/jobs/start"

for env in filtered_envs:
    env_id = env["id"]

    job_payload = {
        "projectId": DOMINO_PROJECT_ID,
        "commandToRun": f"package_inventory-V2.py --env_id {env_id}",
        "title": "list packages",
        "environmentId": env_id
    }

    job_response = requests.post(JOB_URL, headers=HEADERS, data=json.dumps(job_payload))

    if job_response.status_code == 200:
        job_id = job_response.json()["id"]
        print(f"✅ Job started for environment {env_id} (Job ID: {job_id})")
    else:
        print(f"❌ Failed to start job for environment {env_id}: {job_response.text}")
