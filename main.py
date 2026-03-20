import sys
import os

# Ensure the directory containing main.py is in the search path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))


print(f"Current Directory: {os.getcwd()}")
print(f"Directory Contents: {os.listdir('.')}")
print(f"S2B Contents: {os.listdir('S2B')}")
from S2B.scanButton import render_scan_buttons
from SDS.SDS_3 import render_sds3_widgets
import streamlit as st
import pandas as pd
from usps_utils import run_usps_tracking_process
from S2B.scan import push_delivery_print
from SDS.buttons import render_SDS_3_fetch_button   
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


render_scan_buttons(order_ids=edited_df["Order ID"].tolist())

render_SDS_3_fetch_button()

render_sds3_widgets()