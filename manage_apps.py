import os
import requests
import logging
import csv
import argparse

# Read API key from environment variable
api_key = os.getenv("DOMINO_USER_API_KEY")

if not api_key:
    raise ValueError("API key is not set in the environment variable DOMINO_USER_API_KEY")

# Base URL
domino_url = "https://your-domino"

# Headers
headers = {
    "accept": "application/json",
    "X-Domino-Api-Key": api_key
}

def fetch_all_apps():
    """Fetches all apps from Domino."""
    url = f"{domino_url}/v4/modelProducts"
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        logging.debug("Apps fetched successfully")
        apps = response.json()
        return apps
    else:
        logging.error(f"Failed to fetch apps: {response.status_code}")
        return []

def fetch_running_apps():
    """Fetches only running apps."""
    all_apps = fetch_all_apps()
    running_apps = [app for app in all_apps if app.get("status") == "Running"]
    return running_apps

def stop_apps(running_apps):
    """Stops all running apps."""
    stopped_apps = []
    for app in running_apps:
        model_product_id = app.get("id")
        if model_product_id:
            url = f"{domino_url}/v4/modelProducts/{model_product_id}/stop"
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                logging.info(f"Successfully stopped app: {app.get('name')}")
                app['status'] = "Stopped"  # Mark as stopped
                stopped_apps.append(app)
            else:
                logging.error(f"Failed to stop app {app.get('name')}: {response.status_code}")
        else:
            logging.warning(f"App {app.get('name')} has no model product ID")
    return stopped_apps

def write_to_csv(apps, output_file):
    """Writes app details to a CSV file."""
    try:
        with open(output_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["name", "fullName", "email", "status", "modelProductId", "environmentId", "hardwareTierId"])

            for app in apps:
                name = app.get("name", "")
                publisher = app.get("publisher", {})
                
                # Ensure that publisher is not None before accessing its fields
                full_name = publisher.get("fullName", "") if publisher else ""
                email = publisher.get("email", "") if publisher else ""
                status = app.get("status", "")
                model_product_id = app.get("id", "")
                environment_id = app.get("environmentId", "")
                hardware_tier_id = app.get("hardwareTierId", "")

                # Write to CSV file
                writer.writerow([name, full_name, email, status, model_product_id, environment_id, hardware_tier_id])

    except Exception as e:
        logging.error(f"Error writing to CSV: {e}")

def read_stopped_apps_csv(file_path):
    """Reads the stopped apps from the CSV file."""
    stopped_apps = []
    try:
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                stopped_apps.append(row)
    except Exception as e:
        logging.error(f"Error reading stopped apps from CSV: {e}")
    return stopped_apps

def start_stopped_apps(stopped_apps):
    """Starts the apps that were previously stopped."""
    for app in stopped_apps:
        model_product_id = app.get("modelProductId")
        environment_id = app.get("environmentId")
        hardware_tier_id = app.get("hardwareTierId")

        if model_product_id and environment_id and hardware_tier_id:
            url = f"{domino_url}/v4/modelProducts/{model_product_id}/start"
            body = {
                "environmentId": environment_id,
                "hardwareTierId": hardware_tier_id,
                "externalVolumeMountIds": []
            }
            response = requests.post(url, json=body, headers=headers)
            if response.status_code == 200:
                logging.info(f"Successfully started app: {app.get('name')}")
            else:
                logging.error(f"Failed to start app {app.get('name')}: {response.status_code}")
        else:
            logging.warning(f"App {app.get('name')} is missing required fields to start")

def main():
    """Main function to handle the process."""
    parser = argparse.ArgumentParser(description="Manage Domino Apps")
    parser.add_argument("--list", action="store_true", help="List all running apps")
    parser.add_argument("--stop", action="store_true", help="Stop all running apps")
    parser.add_argument("--start-all-stopped", action="store_true", help="Start all stopped apps from CSV")
    parser.add_argument("--dry-run", action="store_true", help="Only list apps without stopping them")
    parser.add_argument("--output", type=str, default="all_apps.csv", help="CSV file for storing app details")
    parser.add_argument("--stopped-output", type=str, default="stopped_apps.csv", help="CSV file for storing stopped apps details")

    args = parser.parse_args()

    logging.basicConfig(filename='manage_apps_log.txt', level=logging.DEBUG)

    running_apps = fetch_running_apps()
    all_apps = fetch_all_apps()
    
    if args.list:
        # Print the running apps' name, full name, email, and status
        print("Running apps:")
        for app in running_apps:
            name = app.get("name", "")
            publisher = app.get("publisher", {})
            full_name = publisher.get("fullName", "") if publisher else ""
            email = publisher.get("email", "") if publisher else ""
            status = app.get("status", "")

            print(f"Name: {name}, Full Name: {full_name}, Email: {email}, Status: {status}")

        # Write running apps details to the CSV file
        write_to_csv(all_apps, args.output)
        print(f"Running apps have been written to {args.output}")

    if args.stop:
        if not args.dry_run:
            confirmation = input("Are you sure you want to stop all running apps? (yes/no): ")
            if confirmation.lower() == "yes":
                stopped_apps = stop_apps(running_apps)
                write_to_csv(stopped_apps, args.stopped_output)
                print(f"Stopped apps have been written to {args.stopped_output}")
            else:
                print("Operation cancelled.")
        else:
            # Dry-run: Print detailed information
            print("Dry run: The following apps will be stopped:")
            for app in running_apps:
                name = app.get("name", "Unknown")
                status = app.get("status", "Unknown")
                print(f"Name: {name}, Status: {status}")

    if args.start_all_stopped:
        stopped_apps = read_stopped_apps_csv(args.stopped_output)
        if stopped_apps:
            start_stopped_apps(stopped_apps)
            print("Started all stopped apps.")
        else:
            print("No stopped apps found to start.")

if __name__ == "__main__":
    main()
