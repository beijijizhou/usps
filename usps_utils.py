import requests
import time
import streamlit as st

def get_access_token(client_id, client_secret):
    url = "https://apis.usps.com/oauth2/v3/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("access_token")

def track_packages(token, tracking_numbers):
    url = "https://apis.usps.com/tracking/v3r2/tracking"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = [{"trackingNumber": str(tn).strip()} for tn in tracking_numbers if tn.strip()]
    response = requests.post(url, json=payload, headers=headers)
    print(f"API Request Sent: {len(payload)} tracking numbers. Status Code: {response.status_code}")
    return response.json()

def run_usps_tracking_process(df, progress_bar=None, status_text=None):
    """
    Business logic for tracking. Updates progress_bar and status_text UI 
    if provided by the caller.
    """
    # 0. Internal Credentials
    client_id = st.secrets["USPS_CLIENT_ID"]
    client_secret = st.secrets["USPS_CLIENT_SECRET"]

    # 1. Data Cleaning & Filtering
    df_clean = df.fillna("").astype(str)
    valid_data = df_clean[
        (df_clean["Tracking Number"].str.startswith("9")) & 
        (df_clean["Tracking Number"].str.len() >= 10)
    ]
    # print(f"Found {len(valid_data)} valid USPS tracking numbers to process.")
    if valid_data.empty:
        return []

    tracking_list = valid_data["Tracking Number"].tolist()
    order_map = dict(zip(valid_data["Tracking Number"], valid_data["Order ID"]))
    total_items = len(tracking_list)
    
    # 2. Authorization
    token = get_access_token(client_id, client_secret)
    results = []
    batch_size = 35

    # 3. Batch Loop with UI Updates
    for i in range(0, total_items, batch_size):
        # Calculate percentage (0.0 to 1.0)
        percent_val = i / total_items
        
        # Update UI Elements
        if progress_bar:
            progress_bar.progress(percent_val, text=f"Progress: {int(percent_val * 100)}%")
        if status_text:
            status_text.info(f"Processing batch {i} of {total_items}...")

        # Execute API Request
        batch = tracking_list[i : i + batch_size]
        batch_results = track_packages(token, batch)
        print(f"Batch {i // batch_size + 1}: Received response for {len(batch_results)} packages.")
        if isinstance(batch_results, list):
            for package in batch_results:
                num = package.get('trackingNumber')
                events = package.get('trackingEvents', [])
                
                # Extract Location and Time
                city, state, zip_c, last_time = "N/A", "N/A", "N/A", "N/A"
                if events:
                    latest = events[0]
                    city = latest.get('eventCity', 'N/A')
                    state = latest.get('eventState', 'N/A')
                    zip_c = latest.get('eventZIPCode', 'N/A')
                    raw_time = latest.get('eventDateTime') or latest.get('eventTimestamp') or "N/A"
                    if raw_time != "N/A":
                        last_time = raw_time.replace('T', ' ').split('.')[0]

                results.append({
                    "Order ID": order_map.get(num, "N/A"),
                    "Tracking Number": num,
                    "Status": package.get('status', 'Unknown'),
                    "Last Updated": last_time,
                    "Location": f"{city}, {state} {zip_c}"
                })
        
        time.sleep(0.01) # Respect rate limits

    # 4. Finalize UI
    if progress_bar:
        progress_bar.progress(1.0, text="Progress: 100%")
    if status_text:
        status_text.success(f"Tracked {total_items} items successfully.")

    return results