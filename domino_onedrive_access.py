import requests
import webbrowser
import os
from msal import PublicClientApplication

# Azure AD Credentials (No Client Secret required)
CLIENT_ID = "client ID from teh Azure app"
TENANT_ID = "Tenant ID from teh Azure app"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# Microsoft Graph API Endpoint
GRAPH_URL = "https://graph.microsoft.com/v1.0"
SCOPES = ["Files.ReadWrite.All", "User.Read"]

# Initialize MSAL Public Client for User Login (No Client Secret)
app = PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

# Try to get an existing token from cache
accounts = app.get_accounts()
if accounts:
    result = app.acquire_token_silent(SCOPES, account=accounts[0])
else:
    # Open browser for user login (Device Code Flow)
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" in flow:
        print(f"\n🔗 Go to this URL: {flow['verification_uri']}")
        print(f"🔑 Enter the code: {flow['user_code']}")
        webbrowser.open(flow["verification_uri"])
        result = app.acquire_token_by_device_flow(flow)
    else:
        print("❌ Device flow failed:", flow)
        exit()

# Check if authentication was successful
if "access_token" in result:
    headers = {"Authorization": f"Bearer {result['access_token']}"}
else:
    print("❌ Authentication failed:", result.get("error_description"))
    exit()

# Function to list OneDrive files
def list_files():
    print("\n📂 Fetching OneDrive Files...")
    response = requests.get(f"{GRAPH_URL}/me/drive/root/children", headers=headers)

    if response.status_code == 200:
        files = response.json().get("value", [])
        if not files:
            print("📁 No files found in OneDrive.")
            return []
        for idx, item in enumerate(files):
            print(f"{idx + 1}. 📄 {item['name']} (ID: {item['id']})")
        return files
    else:
        print("❌ Error fetching files:", response.json())
        return []

# Function to download a file
def download_file():
    files = list_files()
    if not files:
        return
    
    try:
        choice = int(input("\n📥 Enter the number of the file to download: ")) - 1
        if choice < 0 or choice >= len(files):
            print("❌ Invalid choice. Try again.")
            return

        file_id = files[choice]["id"]
        file_name = files[choice]["name"]
        download_url = f"{GRAPH_URL}/me/drive/items/{file_id}/content"
        file_response = requests.get(download_url, headers=headers)

        with open(file_name, "wb") as file:
            file.write(file_response.content)
        print(f"✅ {file_name} downloaded successfully!")
    except ValueError:
        print("❌ Please enter a valid number.")

# Function to upload a file
def upload_file():
    file_path = input("\n📤 Enter the full path of the file to upload: ")

    if not os.path.exists(file_path):
        print("❌ File does not exist. Try again.")
        return

    file_name = os.path.basename(file_path)
    upload_url = f"{GRAPH_URL}/me/drive/root:/{file_name}:/content"

    with open(file_path, "rb") as upload_file:
        upload_response = requests.put(upload_url, headers=headers, data=upload_file)

    if upload_response.status_code in [200, 201]:
        print(f"✅ {file_name} uploaded successfully!")
    else:
        print("❌ Error uploading file:", upload_response.json())

# Menu for user to choose actions
while True:
    print("\n🔹 Choose an action:")
    print("1️⃣ List OneDrive Files")
    print("2️⃣ Download a File")
    print("3️⃣ Upload a File")
    print("4️⃣ Exit")

    choice = input("Enter your choice (1-4): ")

    if choice == "1":
        list_files()
    elif choice == "2":
        download_file()
    elif choice == "3":
        upload_file()
    elif choice == "4":
        print("👋 Exiting program. Goodbye!")
        break
    else:
        print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
