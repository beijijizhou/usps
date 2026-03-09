import streamlit as st
import pandas as pd
import time
import requests
from usps_utils import get_access_token, track_packages
# from gofo_utils import track_gofo_web_api
st.set_page_config(layout="wide", page_title="USPS Bulk Tracker")

st.title("📦 USPS Bulk Tracking Tool")

# 1. Create an empty starting sheet (2 columns)
if 'df_input' not in st.session_state:
    st.session_state.df_input = pd.DataFrame(
        [{"Order ID": "", "Tracking Number": ""}],
    )

st.subheader("Step 1: Paste your data below")
st.caption(
    "You can copy/paste directly from Excel or Google Sheets into this table.")

# The Data Editor acts as your "Spreadsheet" input
edited_df = st.data_editor(
    st.session_state.df_input,
    num_rows="dynamic",  # Allows users to add/delete rows
    width='stretch',
    column_config={
        "Order ID": st.column_config.TextColumn("Order ID", help="Your internal reference"),
        "Tracking Number": st.column_config.TextColumn("Tracking Number (Required)", help="Paste USPS tracking here")
    }
)



# 2. Process Button
if st.button("Start Tracking", type="primary"):
    # Filter out any rows where the tracking number is empty
    df_clean = edited_df.fillna("").astype(str)
    valid_data = df_clean[df_clean["Tracking Number"].str.strip() != ""]
    if valid_data.empty:
        st.warning("Please enter at least one Tracking Number in the table.")
    else:
        try:
            cid = st.secrets["USPS_CLIENT_ID"]
            csec = st.secrets["USPS_CLIENT_SECRET"]

            with st.spinner("Authorizing..."):
                token = get_access_token(cid, csec)
            valid_usps_data = df_clean[
                (df_clean["Tracking Number"].str.startswith("9")) &
                (df_clean["Tracking Number"].str.len() >= 20)
            ]
            usps_tracking_list = valid_usps_data["Tracking Number"].tolist()
            order_map = dict(
                zip(valid_usps_data["Tracking Number"], valid_usps_data["Order ID"]))

            results_accumulator = []
            progress_bar = st.progress(0)

            batch_size = 35
            for i in range(0, len(usps_tracking_list), batch_size):
                batch = usps_tracking_list[i: i + batch_size]
                batch_results = track_packages(token, batch)

                for package in batch_results:
                    num = package.get('trackingNumber')
                    events = package.get('trackingEvents', [])

                    # Formatting the data
                    city, state, zip_c, last_time = "N/A", "N/A", "N/A", "N/A"
                    if events:
                        latest = events[0]
                        city = latest.get('eventCity', 'N/A')
                        state = latest.get('eventState', 'N/A')
                        zip_c = latest.get('eventZIPCode', 'N/A')
                        # print(events)
                        raw_time = latest.get('eventDateTime') or latest.get(
                            'eventTimestamp') or "N/A"
                        print(latest)
                        if raw_time != "N/A":
                            last_time = raw_time.replace('T', ' ').split('.')[
                                0].replace('Z', '')

                    results_accumulator.append({
                        "Order ID": order_map.get(num, "N/A"),
                        "Tracking Number": num,
                        "Status": package.get('status', 'Unknown'),
                        "Last Updated": last_time,
                        "Location": f"{city}, {state} {zip_c}"
                    })

                progress_bar.progress((i + len(batch)) / len(usps_tracking_list))
                time.sleep(0.1)

            st.success("Success!")
            final_df = pd.DataFrame(results_accumulator)
            st.dataframe(final_df, width=1500)

            csv = final_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Results", csv,
                               "usps_report.csv", "text/csv")

        except Exception as e:
            st.error(f"Error: {e}")
