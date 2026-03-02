import streamlit as st
import time
import pandas as pd
from usps_utils import get_access_token, track_packages

st.set_page_config(layout="wide", page_title="USPS Tracker", page_icon="📦")
st.title("📦 USPS Bulk Tracking Tool")
user_input = st.text_area(
    "Paste tracking numbers here:",
    placeholder="92...\n94...",
    height=200
)

if st.button("Track Packages"):
    if not user_input.strip():
        st.warning("Please enter at least one tracking number.")
    else:
        try:
            cid = st.secrets["USPS_CLIENT_ID"]
            csec = st.secrets["USPS_CLIENT_SECRET"]
            
            with st.spinner("Logging into USPS..."):
                token = get_access_token(cid, csec)
                
            raw_list = user_input.replace(',', '\n').splitlines()
            tracking_list = list(dict.fromkeys([line.strip() for line in raw_list if line.strip()]))
            
            total_items = len(tracking_list)
            st.info(f"Processing {total_items} numbers...")

            # Add a progress bar for the batches
            progress_bar = st.progress(0)
            
            batch_size = 35
            results_accumulator = []

            for i in range(0, total_items, batch_size):
                batch = tracking_list[i : i + batch_size]
                batch_results = track_packages(token, batch)
                
                for package in batch_results:
                    num = package.get('trackingNumber')
                    status = package.get('status', 'Unknown')
                    events = package.get('trackingEvents', [])
                    
                    # Initialize default values
                    city, state, zip_code, last_updated = "N/A", "N/A", "N/A", "N/A"
                    
                    if events:
                        latest = events[0]
                        city = latest.get('eventCity', 'N/A')
                        state = latest.get('eventState', 'N/A')
                        zip_code = latest.get('eventZIPCode', 'N/A')
                        # Extract and format the time
                        raw_time = latest.get('eventTimestamp', 'N/A')
                        print(events)
                        if raw_time != "N/A":
                            # Simplifies '2026-03-02T13:27:00Z' to '2026-03-02 13:27'
                            last_updated = raw_time.replace('T', ' ').split('.')[0].replace('Z', '')

                    results_accumulator.append({
                        "Tracking Number": num,
                        "Status": status,
                        "Last Updated": last_updated, # Added this
                        "City": city,
                        "State": state,
                        "ZIP": zip_code
                    })
                
                # Update progress bar
                progress = min((i + batch_size) / total_items, 1.0)
                progress_bar.progress(progress)
                time.sleep(0.5)

            st.success("Tracking Complete!")
            
            # Display results in a clean table
            df = pd.DataFrame(results_accumulator)
            st.dataframe(df, use_container_width=True)

            # Optional: Add download button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download as CSV", csv, "tracking_results.csv", "text/csv")

        except Exception as e:
            st.error(f"An error occurred: {e}")