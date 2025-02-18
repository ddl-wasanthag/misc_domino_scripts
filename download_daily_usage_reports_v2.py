# pip instll openpyxl
# python3 download_daily_usage_reports.py --domain <your domino Ex: prod-field.cs.domino.tech> --api-key <your Domino api key>  --start-date 2/1/2025 --end-date 02/03/2025  --max-retries 3 --retry-delay 30

#!/usr/bin/env python3
import argparse
import requests
import sys
import pandas as pd
import io
import time
from datetime import datetime, timedelta

def generate_daily_report(domain, api_key, report_date, prefix, max_retries, retry_delay):
    """
    Generate the report for a single day (report_date) where the start-date and end-date are the same.
    Implements a retry mechanism if the API call is unsuccessful.
    """
    # Format the date as needed by the API (e.g., mm/dd/yyyy)
    date_str = report_date.strftime("%m/%d/%Y")
    url = f"https://{domain}/admin/generateUsageReport"
    
    headers = {
        "X-Domino-Api-Key": api_key,
        "Accept": "text/csv",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "start-date": date_str,
        "end-date": date_str
    }
    
    attempt = 0
    while attempt < max_retries:
        try:
            response = requests.post(url, headers=headers, data=data)
        except requests.exceptions.RequestException as e:
            print(f"[{date_str}] Attempt {attempt + 1}/{max_retries}: An error occurred during the request: {e}", file=sys.stderr)
            attempt += 1
            if attempt < max_retries:
                print(f"Retrying after {retry_delay} seconds...")
                time.sleep(retry_delay)
            continue

        if response.ok:
            break  # Successful API call
        else:
            print(f"[{date_str}] Attempt {attempt + 1}/{max_retries}: Failed to generate report. Status code: {response.status_code}", file=sys.stderr)
            attempt += 1
            if attempt < max_retries:
                print(f"Retrying after {retry_delay} seconds...")
                time.sleep(retry_delay)
            continue

    # If after all retries we still don't have a successful response, log the error.
    if attempt == max_retries and not response.ok:
        print(f"[{date_str}] All {max_retries} attempts failed.", file=sys.stderr)
        return False

    # Process the CSV response
    try:
        csv_data = response.text
        df = pd.read_csv(io.StringIO(csv_data))
    except Exception as e:
        print(f"[{date_str}] Error parsing CSV data: {e}", file=sys.stderr)
        return False
    
    # Create a safe filename using the date (format: mm-dd-yyyy)
    safe_date = report_date.strftime("%m-%d-%Y")
    output_file = f"{prefix}_{safe_date}.xlsx"
    
    try:
        df.to_excel(output_file, index=False)
        print(f"[{date_str}] Report saved to {output_file}")
    except Exception as e:
        print(f"[{date_str}] Failed to write XLSX file: {e}", file=sys.stderr)
        return False

    return True

def main():
    parser = argparse.ArgumentParser(
        description="Generate daily Domino usage reports (CSV -> XLSX) for a specified date range with a retry mechanism."
    )
    parser.add_argument(
        "--domain",
        required=True,
        help="Your Domino domain (e.g., your-domino.com)"
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="Your Domino API key"
    )
    parser.add_argument(
        "--start-date",
        required=True,
        help="Start date (mm/dd/yyyy), e.g., 2/1/2025"
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="End date (mm/dd/yyyy), e.g., 2/5/2025"
    )
    parser.add_argument(
        "--prefix",
        default="usage_report",
        help="Optional prefix for output filenames (default: 'usage_report'). Files will be named <prefix>_mm-dd-yyyy.xlsx."
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retries for the API call if unsuccessful (default: 3)."
    )
    parser.add_argument(
        "--retry-delay",
        type=int,
        default=30,
        help="Delay in seconds between retries (default: 30 seconds)."
    )
    args = parser.parse_args()
    
    # Parse the input dates
    try:
        start_dt = datetime.strptime(args.start_date, "%m/%d/%Y")
        end_dt = datetime.strptime(args.end_date, "%m/%d/%Y")
    except ValueError as e:
        print(f"Error parsing dates: {e}", file=sys.stderr)
        sys.exit(1)
    
    if start_dt > end_dt:
        print("Error: Start date must be earlier than or equal to the end date.", file=sys.stderr)
        sys.exit(1)
    
    # Loop over each day in the date range (inclusive)
    current_dt = start_dt
    while current_dt <= end_dt:
        success = generate_daily_report(
            args.domain,
            args.api_key,
            current_dt,
            args.prefix,
            args.max_retries,
            args.retry_delay
        )
        if not success:
            print(f"Failed to generate report for {current_dt.strftime('%m/%d/%Y')}.", file=sys.stderr)
        # Move to the next day
        current_dt += timedelta(days=1)

if __name__ == "__main__":
    main()
