import requests
import time
import os
from dotenv import load_dotenv

# Load the variables from .env
load_dotenv()

CLIENT_ID = os.getenv("USPS_CLIENT_ID")
CLIENT_SECRET = os.getenv("USPS_CLIENT_SECRET")
# --- CONFIGURATION ---

TOKEN_URL = "https://apis.usps.com/oauth2/v3/token"
TRACK_URL = "https://apis.usps.com/tracking/v3r2/tracking"

# Your raw list of tracking numbers
raw_data = "9300111038800047184277,9300111038800047184291,9300111038800047184284" # Add full list here

def get_access_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, json=payload)
    response.raise_for_status()
    return response.json().get("access_token")

def track_packages(token, tracking_numbers):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Format for v3 API: list of objects [{"trackingNumber": "..."}]
    payload = [{"trackingNumber": str(tn).strip()} for tn in tracking_numbers if tn.strip()]
    
    response = requests.post(TRACK_URL, json=payload, headers=headers)
    return response.json()

# 1. Clean the list (remove empty strings/commas)
tracking_list = [x for x in raw_data.split(',') if x.strip()]

# 2. Get the Token
try:
    token = get_access_token()
    print("✓ Token acquired successfully.\n")

    # 3. Batch process (USPS Limit: 35 per request)
    batch_size = 35
    for i in range(0, len(tracking_list), batch_size):
        batch = tracking_list[i : i + batch_size]
        print(f"Querying batch {i//batch_size + 1} ({len(batch)} numbers)...")
        
        results = track_packages(token, batch)
        
        # Process your results here
        print(results) 
        
        # Short pause to be kind to the API
        time.sleep(1)

except Exception as e:
    print(f"Error: {e}")