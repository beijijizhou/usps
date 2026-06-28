# DEBUG INFO
from SDS.buttons import render_SDS_3_fetch_button
from Humbird.button import render_humbird_workflow
from rbt.rbt_button_ui import render_rbt_button_ui
from usps_utils import run_usps_tracking_process
import pandas as pd
import streamlit as st
from s2b.scanButton import render_scan_buttons
import os
import sys
from usps_batch_ui import render_usps_batch_tables

from utility import get_data_metrics
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Add that directory to the very beginning of the Python path
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
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




c1, c2, _ = st.columns([2, 2, 4])
with c1:
    sort_by = st.selectbox("Sort by:", ["None", "Order ID", "Tracking Number"])
with c2:
    # A button to apply the sorting manually
    if st.button("🔄 Apply Sort", use_container_width=True):
        if sort_by == "Order ID":
            st.session_state.df_input = st.session_state.df_input.sort_values(by="Order ID").reset_index(drop=True)
            st.rerun()
        elif sort_by == "Tracking Number":
            st.session_state.df_input = st.session_state.df_input.sort_values(by="Tracking Number").reset_index(drop=True)
            st.rerun()
edited_df = st.data_editor(
    st.session_state.df_input,
    num_rows="dynamic",  # Allows users to add/delete rows
    width='stretch',
    column_config={
        "Order ID": st.column_config.TextColumn("Order ID"),
        "Tracking Number": st.column_config.TextColumn("Tracking Number (Required)"),
    }
)
# if edited_df is not None:
#     st.session_state.df_input = edited_df
c1, c2 = st.columns(2)
count_orders, count_tracking = get_data_metrics(st.session_state.df_input)

c1.metric("📦 Total Order IDs", count_orders)
c2.metric("🚚 Total Tracking Numbers", count_tracking)
# 2. Process Button
lookup_col, api_col = st.columns(2)
with lookup_col:
    build_batches = st.button("Build USPS Website Batches", type="primary", use_container_width=True)
with api_col:
    start_api_tracking = st.button("Start Paid USPS API Tracking", use_container_width=True)

if build_batches:
    df_clean = edited_df.fillna("").astype(str)
    valid_data = df_clean[df_clean["Tracking Number"].str.strip() != ""]
    if valid_data.empty:
        st.warning("Please enter at least one Tracking Number in the table.")
    else:
        st.session_state.usps_website_source_df = valid_data

if start_api_tracking:
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

if "usps_website_source_df" in st.session_state:
    st.subheader("Step 2: USPS website batches")
    render_usps_batch_tables(
        st.session_state.usps_website_source_df,
        key_prefix="main_pasted_table",
        expanded=True
    )


render_scan_buttons(order_ids=edited_df["Order ID"].tolist())

# render_SDS_3_fetch_button()

# render_sds3_widgets()
render_humbird_workflow()



render_rbt_button_ui()
