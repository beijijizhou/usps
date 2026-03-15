from courier.shipping_controller import run_shipping_controller
import streamlit as st
import pandas as pd

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
if st.button("Track Shipments"):
    p_bar = st.progress(0)
    msg = st.empty()
    
    # You can loop through multiple couriers easily
    results = []
    for carrier in ["GOFO", "USPS"]:
        results.extend(run_shipping_controller(edited_df, carrier, p_bar, msg))
    
    if results:
        st.success("All Tracking Finished!")
        st.dataframe(pd.DataFrame(results))
