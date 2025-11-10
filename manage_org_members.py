#!/usr/bin/env python3
"""
Domino Organization Member Management Script

This script manages organization membership in Domino by adding or removing users
based on a list of usernames provided in a text file.

Usage:
    python manage_org_members.py --action add --user-file ./users.txt --org myorg
    python manage_org_members.py --action remove --user-file ./users.txt --org myorg
    python manage_org_members.py --action add --user-file ./users.txt --org myorg --dry-run
"""

import argparse
import logging
import sys
import os
from typing import List, Dict, Optional, Set
from datetime import datetime
import requests
import json


class DominoOrgManager:
    """Manages Domino organization membership operations."""
    
    def __init__(self, base_url: str, api_token: str, log_file: str = None, user_limit: int = 10000):
        """
        Initialize the Domino Organization Manager.
        
        Args:
            base_url: Base URL for Domino API (e.g., https://cloud-cx.domino.tech)
            api_token: API authentication token
            log_file: Optional log file path
            user_limit: Maximum number of users to fetch (default: 10000)
        """
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.user_limit = user_limit
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Domino-Api-Key': api_token
        })
        
        # Setup logging
        self._setup_logging(log_file)
        
    def _setup_logging(self, log_file: Optional[str]):
        """Configure logging to both console and file."""
        # Create logger
        self.logger = logging.getLogger('DominoOrgManager')
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        # Console handler (INFO and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (DEBUG and above)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(file_handler)
        else:
            # Default log file with timestamp
            default_log = f"domino_org_manager_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(default_log)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(file_handler)
            self.logger.info(f"Logging to file: {default_log}")
    
    def get_users_batch(self, usernames: List[str]) -> Dict[str, Optional[str]]:
        """
        Fetch user IDs for a list of usernames efficiently.
        Fetches all users once and filters in memory.
        
        Args:
            usernames: List of usernames to look up
            
        Returns:
            Dictionary mapping username to user ID (None if not found)
        """
        self.logger.info(f"Fetching users for batch lookup of {len(usernames)} usernames...")
        
        # Fetch all users with configured limit
        url = f"{self.base_url}/api/users/v1/users?limit={self.user_limit}"
        
        try:
            self.logger.debug(f"API Call: GET {url}")
            response = self.session.get(url)
            self.logger.debug(f"API Response Status: {response.status_code}")
            self.logger.debug(f"API Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            data = response.json()
            
            users_count = len(data.get('users', []))
            self.logger.debug(f"API Response: Retrieved {users_count} users (body not logged due to size)")
            
            # Build a mapping of all users
            all_users_map = {}
            for user in data.get('users', []):
                username = user.get('userName')
                user_id = user.get('id')
                if username and user_id:
                    all_users_map[username] = user_id
            
            self.logger.info(f"Retrieved {len(all_users_map)} total users from Domino")
            
            # Filter to only requested usernames
            result = {}
            for username in usernames:
                result[username] = all_users_map.get(username)
                if result[username]:
                    self.logger.debug(f"Found user {username} with ID: {result[username]}")
                else:
                    self.logger.debug(f"User not found: {username}")
            
            found_count = sum(1 for v in result.values() if v is not None)
            self.logger.info(f"Found {found_count} out of {len(usernames)} requested users")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch users: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.debug(f"Error Response Status: {e.response.status_code}")
                self.logger.debug(f"Error Response Body: {e.response.text}")
            raise
    
    def get_all_users(self, limit: int = 10000) -> Dict[str, str]:
        """
        Fetch all users and create a username to user ID mapping.
        Note: This method is kept for backward compatibility.
        
        Args:
            limit: Maximum number of users to fetch (default: 10000)
        
        Returns:
            Dictionary mapping username to user ID
        """
        self.logger.info(f"Fetching all users from Domino (limit: {limit})...")
        url = f"{self.base_url}/api/users/v1/users?limit={limit}"
        
        try:
            self.logger.debug(f"API Call: GET {url}")
            response = self.session.get(url)
            self.logger.debug(f"API Response Status: {response.status_code}")
            self.logger.debug(f"API Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            data = response.json()
            
            # Don't log full response body for large user lists
            users_count = len(data.get('users', []))
            self.logger.debug(f"API Response: Retrieved {users_count} users (body not logged due to size)")
            
            user_map = {}
            for user in data.get('users', []):
                username = user.get('userName')
                user_id = user.get('id')
                if username and user_id:
                    user_map[username] = user_id
            
            self.logger.info(f"Retrieved {len(user_map)} users")
            self.logger.debug(f"User map sample (first 5): {list(user_map.items())[:5]}")
            return user_map
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch users: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.debug(f"Error Response Status: {e.response.status_code}")
                self.logger.debug(f"Error Response Body: {e.response.text}")
            raise
    
    def get_organization_info(self, org_name: str) -> Optional[Dict]:
        """
        Get organization information including current members.
        
        Args:
            org_name: Name of the organization
            
        Returns:
            Organization data or None if not found
        """
        self.logger.info(f"Fetching organization info for: {org_name}")
        url = f"{self.base_url}/api/organizations/v1/organizations/all?nameFilter={org_name}"
        
        try:
            self.logger.debug(f"API Call: GET {url}")
            response = self.session.get(url)
            self.logger.debug(f"API Response Status: {response.status_code}")
            self.logger.debug(f"API Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            data = response.json()
            self.logger.debug(f"API Response Body: {json.dumps(data, indent=2)}")
            
            orgs = data.get('orgs', [])
            if not orgs:
                self.logger.error(f"Organization '{org_name}' not found")
                return None
            
            # Find exact match
            for org in orgs:
                if org.get('name') == org_name:
                    self.logger.info(f"Found organization: {org_name} (ID: {org.get('id')})")
                    self.logger.debug(f"Organization has {len(org.get('members', []))} members")
                    return org
            
            self.logger.error(f"Organization '{org_name}' not found (no exact match)")
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch organization info: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.debug(f"Error Response Status: {e.response.status_code}")
                self.logger.debug(f"Error Response Body: {e.response.text}")
            raise
    
    def remove_member(self, org_id: str, user_id: str, dry_run: bool = False) -> bool:
        """
        Remove a member from an organization.
        
        Args:
            org_id: Organization ID
            user_id: User ID to remove
            dry_run: If True, don't actually make the change
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/api/organizations/v1/organizations/{org_id}/user?memberToRemoveId={user_id}"
        
        if dry_run:
            self.logger.info(f"[DRY RUN] Would remove user {user_id} from organization {org_id}")
            self.logger.debug(f"[DRY RUN] Would call: DELETE {url}")
            return True
        
        try:
            self.logger.debug(f"API Call: DELETE {url}")
            self.logger.debug(f"Removing user {user_id} from organization {org_id}")
            
            response = self.session.delete(url)
            self.logger.debug(f"API Response Status: {response.status_code}")
            self.logger.debug(f"API Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            data = response.json()
            self.logger.debug(f"API Response Body: {json.dumps(data, indent=2)}")
            self.logger.debug(f"Successfully removed user {user_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to remove user {user_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.debug(f"Error Response Status: {e.response.status_code}")
                self.logger.debug(f"Error Response Body: {e.response.text}")
            return False
    
    def add_member(self, org_id: str, user_id: str, role: str = "Member", dry_run: bool = False) -> bool:
        """
        Add a member to an organization.
        
        Args:
            org_id: Organization ID
            user_id: User ID to add
            role: Organization role (default: "Member")
            dry_run: If True, don't actually make the change
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/api/organizations/v1/organizations/{org_id}/user"
        payload = {
            "organizationRole": role,
            "userId": user_id
        }
        
        if dry_run:
            self.logger.info(f"[DRY RUN] Would add user {user_id} to organization {org_id} with role {role}")
            self.logger.debug(f"[DRY RUN] Would call: PUT {url}")
            self.logger.debug(f"[DRY RUN] Would send payload: {json.dumps(payload, indent=2)}")
            return True
        
        try:
            self.logger.debug(f"API Call: PUT {url}")
            self.logger.debug(f"API Request Payload: {json.dumps(payload, indent=2)}")
            self.logger.debug(f"Adding user {user_id} to organization {org_id} with role {role}")
            
            response = self.session.put(url, json=payload)
            self.logger.debug(f"API Response Status: {response.status_code}")
            self.logger.debug(f"API Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            data = response.json()
            self.logger.debug(f"API Response Body: {json.dumps(data, indent=2)}")
            self.logger.debug(f"Successfully added user {user_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to add user {user_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.debug(f"Error Response Status: {e.response.status_code}")
                self.logger.debug(f"Error Response Body: {e.response.text}")
            return False
    
    def read_usernames_from_file(self, file_path: str) -> List[str]:
        """
        Read usernames from a text file (one per line).
        
        Args:
            file_path: Path to the file containing usernames
            
        Returns:
            List of usernames
        """
        self.logger.info(f"Reading usernames from file: {file_path}")
        
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                usernames = [line.strip() for line in f if line.strip()]
            
            self.logger.info(f"Read {len(usernames)} usernames from file")
            self.logger.debug(f"Usernames: {usernames}")
            return usernames
            
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {e}")
            raise
    
    def manage_members(self, action: str, org_name: str, user_file: str, 
                      dry_run: bool = False, skip_confirmation: bool = False) -> bool:
        """
        Main method to add or remove members from an organization.
        
        Args:
            action: 'add' or 'remove'
            org_name: Name of the organization
            user_file: Path to file containing usernames
            dry_run: If True, show what would be done without doing it
            skip_confirmation: If True, skip confirmation prompt
            
        Returns:
            True if all operations successful, False otherwise
        """
        self.logger.info(f"=" * 80)
        self.logger.info(f"Starting organization member management")
        self.logger.info(f"Action: {action.upper()}")
        self.logger.info(f"Organization: {org_name}")
        self.logger.info(f"User file: {user_file}")
        self.logger.info(f"Dry run: {dry_run}")
        self.logger.info(f"=" * 80)
        
        try:
            # Read usernames from file
            usernames = self.read_usernames_from_file(user_file)
            
            # Get organization info
            org_info = self.get_organization_info(org_name)
            if not org_info:
                return False
            
            org_id = org_info.get('id')
            current_members = {m['userId'] for m in org_info.get('members', [])}
            
            # Batch lookup user IDs (fetches all users once, filters in memory)
            user_lookup = self.get_users_batch(usernames)
            
            # Separate found and missing users
            user_ids_to_process = []
            missing_users = []
            
            for username in usernames:
                user_id = user_lookup.get(username)
                if user_id:
                    user_ids_to_process.append((username, user_id))
                else:
                    missing_users.append(username)
                    self.logger.warning(f"User not found: {username}")
            
            if missing_users:
                self.logger.warning(f"The following users were not found: {', '.join(missing_users)}")
            
            if not user_ids_to_process:
                self.logger.error("No valid users to process")
                return False
            
            # Filter based on action
            if action == 'add':
                # Filter out users already in org
                users_to_process = [(un, uid) for un, uid in user_ids_to_process if uid not in current_members]
                already_members = [(un, uid) for un, uid in user_ids_to_process if uid in current_members]
                
                if already_members:
                    self.logger.info(f"The following users are already members (skipping): "
                                   f"{', '.join([un for un, _ in already_members])}")
            else:  # remove
                # Filter to only users currently in org
                users_to_process = [(un, uid) for un, uid in user_ids_to_process if uid in current_members]
                not_members = [(un, uid) for un, uid in user_ids_to_process if uid not in current_members]
                
                if not_members:
                    self.logger.info(f"The following users are not members (skipping): "
                                   f"{', '.join([un for un, _ in not_members])}")
            
            if not users_to_process:
                self.logger.info(f"No users to {action}")
                return True
            
            # Display summary
            self.logger.info("")
            self.logger.info(f"{'=' * 80}")
            if dry_run:
                self.logger.info(f"[DRY RUN MODE] The following changes WOULD be made:")
            else:
                self.logger.info(f"The following changes will be made:")
            self.logger.info(f"{'=' * 80}")
            self.logger.info(f"Action: {action.upper()} users")
            self.logger.info(f"Organization: {org_name}")
            self.logger.info(f"Number of users: {len(users_to_process)}")
            self.logger.info("")
            self.logger.info("Users:")
            for username, user_id in users_to_process:
                self.logger.info(f"  - {username} (ID: {user_id})")
            self.logger.info(f"{'=' * 80}")
            
            # Confirmation prompt
            if not skip_confirmation and not dry_run:
                self.logger.info("")
                response = input("Do you want to proceed? (yes/no): ").strip().lower()
                if response not in ['yes', 'y']:
                    self.logger.info("Operation cancelled by user")
                    return False
                self.logger.info("")
            
            # Perform operations
            success_count = 0
            failure_count = 0
            
            for username, user_id in users_to_process:
                self.logger.info(f"Processing user: {username}")
                
                if action == 'add':
                    success = self.add_member(org_id, user_id, dry_run=dry_run)
                else:  # remove
                    success = self.remove_member(org_id, user_id, dry_run=dry_run)
                
                if success:
                    success_count += 1
                    if not dry_run:
                        self.logger.info(f"Successfully {action}ed user: {username}")
                else:
                    failure_count += 1
                    self.logger.error(f"Failed to {action} user: {username}")
            
            # Summary
            self.logger.info("")
            self.logger.info(f"{'=' * 80}")
            self.logger.info(f"Operation Summary")
            self.logger.info(f"{'=' * 80}")
            self.logger.info(f"Total users processed: {len(users_to_process)}")
            self.logger.info(f"Successful: {success_count}")
            self.logger.info(f"Failed: {failure_count}")
            if missing_users:
                self.logger.info(f"Users not found: {len(missing_users)}")
            self.logger.info(f"{'=' * 80}")
            
            return failure_count == 0
            
        except Exception as e:
            self.logger.error(f"Unexpected error during operation: {e}", exc_info=True)
            return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Manage Domino organization membership',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Add users to an organization:
    python manage_org_members.py --action add --user-file ./users.txt --org myorg --base-url https://cloud-cx.domino.tech
  
  Remove users from an organization:
    python manage_org_members.py --action remove --user-file ./users.txt --org myorg --base-url https://cloud-cx.domino.tech
  
  Dry run (preview changes without making them):
    python manage_org_members.py --action add --user-file ./users.txt --org myorg --base-url https://cloud-cx.domino.tech --dry-run
  
  Skip confirmation prompt:
    python manage_org_members.py --action remove --user-file ./users.txt --org myorg --base-url https://cloud-cx.domino.tech --yes
        """
    )
    
    parser.add_argument(
        '--action',
        required=True,
        choices=['add', 'remove'],
        help='Action to perform: add or remove users'
    )
    
    parser.add_argument(
        '--user-file',
        required=True,
        help='Path to text file containing usernames (one per line)'
    )
    
    parser.add_argument(
        '--org',
        required=True,
        help='Name of the organization'
    )
    
    parser.add_argument(
        '--base-url',
        required=True,
        help='Base URL for Domino API (e.g., https://cloud-cx.domino.tech)'
    )
    
    parser.add_argument(
        '--api-token',
        help='Domino API token (or set DOMINO_API_TOKEN environment variable)'
    )
    
    parser.add_argument(
        '--user-limit',
        type=int,
        default=10000,
        help='Maximum number of users to fetch from API (default: 10000)'
    )
    
    parser.add_argument(
        '--log-file',
        help='Path to log file (default: auto-generated with timestamp)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without actually making them'
    )
    
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt'
    )
    
    args = parser.parse_args()
    
    # Get API token
    api_token = args.api_token or os.environ.get('DOMINO_API_TOKEN')
    if not api_token:
        print("ERROR: API token not provided. Use --api-token or set DOMINO_API_TOKEN environment variable",
              file=sys.stderr)
        sys.exit(1)
    
    try:
        # Create manager instance
        manager = DominoOrgManager(
            base_url=args.base_url,
            api_token=api_token,
            log_file=args.log_file,
            user_limit=args.user_limit
        )
        
        # Execute operation
        success = manager.manage_members(
            action=args.action,
            org_name=args.org,
            user_file=args.user_file,
            dry_run=args.dry_run,
            skip_confirmation=args.yes
        )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()