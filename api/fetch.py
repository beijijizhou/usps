import streamlit as st
import requests
import time

# --- LOGIC FUNCTIONS ---


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
    payload = [{"trackingNumber": str(tn).strip()}
               for tn in tracking_numbers if tn.strip()]
    response = requests.post(url, json=payload, headers=headers)
    return response.json()


# --- UI SETUP ---
st.set_page_config(page_title="USPS Tracker", page_icon="📦")
st.title("📦 USPS Bulk Tracking Tool")

# 1. User Input Area
user_input = st.text_area(
    "Paste tracking numbers here (one per line or comma-separated):",
    placeholder="92001...\n92001...",
    height=300
)

# 2. Process Button
if st.button("Track Packages"):
    if not user_input.strip():
        st.warning("Please enter at least one tracking number.")
    else:
        try:
            # Use Streamlit Secrets for your credentials
            cid = st.secrets["USPS_CLIENT_ID"]
            csec = st.secrets["USPS_CLIENT_SECRET"]

            with st.spinner("Acquiring token and fetching data..."):
                token = get_access_token(cid, csec)

                # Clean user input: handle newlines and commas, remove duplicates
                raw_list = user_input.replace(',', '\n').splitlines()
                tracking_list = list(dict.fromkeys(
                    [line.strip() for line in raw_list if line.strip()]))

                st.info(
                    f"Found {len(tracking_list)} unique numbers. Querying in batches of 35...")

                # 3. Batch process and Display
                batch_size = 35
                results_accumulator = []

                for i in range(0, len(tracking_list), batch_size):
                    batch = tracking_list[i: i + batch_size]
                    batch_results = track_packages(token, batch)

                    for package in batch_results:
                        num = package.get('trackingNumber')
                        status = package.get('status', 'Unknown')
                        events = package.get('trackingEvents', [])

                        # Get latest event details
                        city, state, zip_code = "N/A", "N/A", "N/A"
                        if events:
                            latest = events[0]
                            city = latest.get('eventCity', 'N/A')
                            state = latest.get('eventState', 'N/A')
                            zip_code = latest.get('eventZIPCode', 'N/A')

                        results_accumulator.append({
                            "Tracking Number": num,
                            "Status": status,
                            "City": city,
                            "State": state,
                            "ZIP": zip_code
                        })

                    time.sleep(0.5)  # Slight delay to be safe

                # 4. Show Results in a Table
                st.success("Tracking Complete!")
                st.dataframe(results_accumulator, width='stretch')

        except Exception as e:
            st.error(f"An error occurred: {e}")
