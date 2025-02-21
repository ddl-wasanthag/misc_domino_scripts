import subprocess
import pandas as pd
import argparse
import os

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Generate software inventory for Python and R packages.")
parser.add_argument("--env_id", required=True, help="Environment ID to be added to the inventory.")
args = parser.parse_args()
env_id = args.env_id  # Capture the environment ID

# Define output CSV file path
output_file = "/domino/datasets/local/onedrive/software_inventory.csv"

# Function to get installed Python packages
def get_python_packages():
    result = subprocess.run(["pip", "list", "--format=freeze"], capture_output=True, text=True)
    packages = [line.split("==") for line in result.stdout.splitlines() if "==" in line]
    return pd.DataFrame(packages, columns=["Package Name", "Version"]).assign(Language="Python", Env_ID=env_id)

# Function to get installed R packages
def get_r_packages():
    r_script = "write.csv(installed.packages()[, c('Package', 'Version')], file='/tmp/r_packages.csv', row.names=FALSE)"
    subprocess.run(["R", "-e", r_script], capture_output=True, text=True)
    
    # Read the R packages CSV file
    df_r = pd.read_csv("/tmp/r_packages.csv")
    df_r.columns = ["Package Name", "Version"]  # Ensure consistent column names
    df_r["Language"] = "R"
    df_r["Env_ID"] = env_id
    return df_r

# Get package lists
df_python = get_python_packages()
df_r = get_r_packages()

# Combine both into one DataFrame
df_combined = pd.concat([df_python, df_r], ignore_index=True)

# Check if the file exists (to avoid duplicate headers)
file_exists = os.path.isfile(output_file)

# Append data to CSV (write header only if file doesn't exist)
df_combined.to_csv(output_file, mode='a', index=False, header=not file_exists)

print(f"✅ Data appended to {output_file}")
