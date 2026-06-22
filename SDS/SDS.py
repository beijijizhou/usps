import streamlit as st
import pandas as pd
import requests
import time
from SDS.QA_scan import scanID
from SDS.auth_api import login_to_qa
from SDS.factoryFetch import factory_fetch_records
import config
from SDS.platform_selector import render_platform_dropdown
from SDS.pre_scan import run_parallel_scan_generator

# Assign to a local variable for shorter typing if you like
QA_TOKEN = "sds-pod:aa324065-3cd0-4790-afab-7615eac1610b"

# --- API Logic ---
def handle_batch_scan(order_ids):
    """
    UI: Manages the progress bar and processes data.
    Takes a local list of order_ids passed directly from the UI trigger.
    """
    if not order_ids:
        st.warning("No valid Order IDs to scan.")
        return

    # 1. Setup UI Elements
    progress_bar = st.progress(0)
    status_text = st.empty()
    scan_log = []
    total = len(order_ids)
    start_time = time.time()

    # 2. Run Generator and Update UI
    for i, res in enumerate(run_parallel_scan_generator(order_ids)):
        order_id = res.get("Order ID")
        success = res.get("status") == "success"
        msg = res.get("msg") or res.get("tracking") 
        carrier_name = res.get("carrier", "")

        if success:
            scanID(order_id)  # Optionally trigger a detailed scan for successful IDs
            scan_log.append({
                "Order ID": order_id,
                "Scan Status": "✅ Success (USPS)",
                "Result": msg
            })
        elif success:
            scan_log.append({
                "Order ID": order_id,
                "Scan Status": "⚠️ Skipped",
                "Result": f"Non-USPS carrier: {carrier_name}"
            })
        else:
            scan_log.append({
                "Order ID": order_id,
                "Scan Status": "❌ Failed",
                "Result": msg
            })

        # Update progress
        percent_complete = (i + 1) / total
        progress_bar.progress(percent_complete)
        status_text.text(f"Processing {i+1}/{total}: {order_id}")

    # 3. Finalize
    duration = time.time() - start_time
    st.session_state.scan_results_summary = pd.DataFrame(scan_log)
    status_text.success(f"Batch scan complete! {total} orders in {duration:.2f}s")
    
    st.rerun()

# --- Streamlit UI ---
def render_SDS_widgets():
    st.divider()
    print(login_to_qa())
    # st.markdown("### 🛠️ SDS 3D 热转印 订单操作")
    render_platform_dropdown()  # Platform selector at the top of the section
    # Initialize a temporary holding state key *only* to bridge the two button clicks
    if "fetched_ids_list" not in st.session_state:
        st.session_state.fetched_ids_list = []

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 获取生产中订单", use_container_width=True):
            with st.spinner("Fetching from SDS..."):
                # Local variable inside the button scope
                local_fetched_ids = factory_fetch_records()
                
                if local_fetched_ids:
                    st.session_state.fetched_ids_list = local_fetched_ids
                    st.success(f"Successfully loaded {len(local_fetched_ids)} orders.")
                else:
                    st.session_state.fetched_ids_list = []
                    st.warning("No orders found.")

    with col2:
        current_orders = st.session_state.fetched_ids_list
        button_disabled = len(current_orders) == 0
        
        if st.button("🚀 执行批量 面单获取", type="primary", use_container_width=True, disabled=button_disabled):
            local_scan_list = list(current_orders)
            
            # Clear the tracking list cache before running a new scan
            st.session_state.fetched_ids_list = []
            handle_batch_scan(local_scan_list)

    # --- Display Fetched Orders First ---
    # If there are fetched IDs in our temporary holding list, show them cleanly here
    if st.session_state.fetched_ids_list:
        st.markdown(f"📋 **待扫描队列 ({len(st.session_state.fetched_ids_list)} 个订单):**")
        
        # Convert the local list into a clean dataframe for display purposes only
        display_df = pd.DataFrame({"Order ID": st.session_state.fetched_ids_list})
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    # --- Summary Display Panel ---
    if "scan_results_summary" in st.session_state:
        with st.expander("📄 查看最近一次扫描详情", expanded=True):
            st.dataframe(st.session_state.scan_results_summary, use_container_width=True)