import streamlit as st
import pandas as pd
import time
import requests
from usps_utils import get_access_token, run_usps_tracking_process, track_packages
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
            status_message = st.empty()
            progress_bar = st.progress(0, text="Initializing...")
            results = run_usps_tracking_process(valid_data, progress_bar=progress_bar,
                                                status_text=status_message)
            if results:
                final_df = pd.DataFrame(results)
                st.dataframe(final_df)
            else:
                st.info("No valid USPS tracking numbers found in the input.")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
