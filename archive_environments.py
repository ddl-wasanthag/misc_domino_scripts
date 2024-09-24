#This script should be run in the following manner
# Make sure to create a environments.txt files with enviornment IDs you want to archive
# Set the MONGODB_USERNAME and MONGODB_PASSWORD as enviornment variables
# If you are using mongo db admin credentails, update authSource="admin"
# Otherwise use authSource="domino"
#
# To review archive changes without actually archiving
# python archive_environments.py --dry-run
# To archive enviornments
# python archive_environments.py --archive
# To unarchive enviornments using MongoDB
# python archive_environments.py --unarchive
#
# The script will create a log file in teh same directory with the same name as the script
# You can control logging level with level=logging.DEBUG or level=logging.INFO



import argparse
import os
import requests
import logging
from pymongo import MongoClient
from bson import ObjectId

# Set up logging to a file named after the script
script_name = os.path.splitext(os.path.basename(__file__))[0]
logging.basicConfig(
    filename=f"{script_name}.log",
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# MongoDB connection setup using platform namespace from config
def connect_mongo():
    platform_namespace = "domino-platform"
    
    try:
        client = MongoClient(
            "mongodb://mongodb-replicaset.{}.svc.cluster.local:27017".format(
                platform_namespace
            ),
            username=os.environ["MONGODB_USERNAME"],
            password=os.environ["MONGODB_PASSWORD"],
            authSource="admin",
            authMechanism="SCRAM-SHA-1",
        )
        return client['domino']  # Assuming the database name is 'domino'
    
    except KeyError as e:
        logging.error(f"Environment variable {str(e)} is missing.")
        print(f"Error: Missing environment variable {str(e)}.")
        return None

# Function to fetch environment details
def get_environment_details(env_id, domino_url):
    url = f"{domino_url}/v4/environments/self"
    headers = {
        "accept": "*/*",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        environments = response.json()
        # Find the environment by id
        for env in environments:
            if env['id'] == env_id:
                return env['name']
    else:
        logging.error(f"Failed to fetch environment details. Status code: {response.status_code}")
    return None

# Function to archive a compute environment
def archive_environment(env_id, env_name, domino_url, dry_run):
    url = f"{domino_url}/v4/environments/{env_id}"
    headers = {
        "accept": "*/*",
        "Content-Type": "application/json"
    }
    data = '{"archived":true}'
    
    if dry_run:
        logging.info(f"[DRY RUN] Environment '{env_name}' (ID: {env_id}) would be archived.")
        print(f"[DRY RUN] Environment '{env_name}' (ID: {env_id}) would be archived.")
    else:
        response = requests.delete(url, headers=headers, data=data)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logging.info(f"Environment '{env_name}' (ID: {env_id}) archived successfully. Message: {result.get('message')}")
                print(f"Environment '{env_name}' (ID: {env_id}) archived successfully. Message: {result.get('message')}")
            else:
                logging.error(f"Failed to archive environment '{env_name}' (ID: {env_id}). Response: {result}")
                print(f"Failed to archive environment '{env_name}' (ID: {env_id}). Response: {result}")
        else:
            logging.error(f"Failed to archive environment '{env_name}' (ID: {env_id}). Status code: {response.status_code}")
            print(f"Failed to archive environment '{env_name}' (ID: {env_id}). Status code: {response.status_code}")

# Function to unarchive a compute environment
def unarchive_environment(env_id, mongo_db):
    try:
        # Convert the string `env_id` to ObjectId
        object_id = ObjectId(env_id)

        # Access the environments_v2 collection
        environments_v2_collection = mongo_db["environments_v2"]

        # Update the document with the matching _id to set "isArchived" to false
        result = environments_v2_collection.update_one(
            {"_id": object_id},
            {"$set": {"isArchived": False}}
        )

        if result.matched_count > 0:
            logging.info(f"Successfully unarchived environment with ID: {env_id}")
            print(f"Successfully unarchived environment with ID: {env_id}")
        else:
            logging.warning(f"No environment found with ID: {env_id}")
            print(f"No environment found with ID: {env_id}")
    except Exception as e:
        logging.error(f"Failed to unarchive environment with ID: {env_id}. Error: {e}")
        print(f"Failed to unarchive environment with ID: {env_id}. Error: {e}")

# Function to read environment IDs from file
def read_environments(file_path):
    with open(file_path, 'r') as f:
        environments = [line.strip() for line in f if line.strip()]
    return environments

def main():
    parser = argparse.ArgumentParser(description="Manage compute environments.")
    parser.add_argument('--file', type=str, default="environments.txt", help="Path to the environments file")
    parser.add_argument('--dry-run', action='store_true', help="List environments to be archived without archiving")
    parser.add_argument('--archive', action='store_true', help="Archive environments listed in the file")
    parser.add_argument('--unarchive', action='store_true', help="Unarchive environments listed in the file")

    args = parser.parse_args()

    # Get the Domino URL from the OS environment variable
    domino_url = os.getenv('DOMINO_API_PROXY')
    if not domino_url:
        logging.error("DOMINO_API_PROXY environment variable is not set.")
        print("Error: DOMINO_API_PROXY environment variable is not set.")
        return

    # Read environments from file
    environments = read_environments(args.file)

    # Connect to MongoDB if unarchiving
    mongo_db = None
    if args.unarchive:
        mongo_db = connect_mongo()
        if mongo_db is None:  # Explicit comparison with None
            return

    # Check if a valid option is selected
    if not (args.dry_run or args.archive or args.unarchive):
        logging.error("You must specify either --dry-run, --archive, or --unarchive.")
        print("You must specify either --dry-run, --archive, or --unarchive.")
        return

    # Process each environment ID
    for env_id in environments:
        if args.unarchive and mongo_db is not None:  # Explicit comparison with None
            unarchive_environment(env_id, mongo_db)
        else:
            # Fetch environment name using /v4/environments/self
            env_name = get_environment_details(env_id, domino_url)
            if env_name:
                if args.dry_run:
                    logging.info(f"[DRY RUN] Environment '{env_name}' (ID: {env_id}) would be archived.")
                    print(f"[DRY RUN] Environment '{env_name}' (ID: {env_id}) would be archived.")
                elif args.archive:
                    archive_environment(env_id, env_name, domino_url, False)
            else:
                logging.warning(f"Environment ID {env_id} not found.")
                print(f"Environment ID {env_id} not found.")

if __name__ == "__main__":
    main()
