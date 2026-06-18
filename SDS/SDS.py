import streamlit as st
import pandas as pd
import requests
import time
from SDS.factoryFetch import factory_fetch_records
import config

from SDS.pre_scan import run_parallel_scan_generator

# Assign to a local variable for shorter typing if you like
QA_TOKEN = "sds-pod:aa324065-3cd0-4790-afab-7615eac1610b"
# print(f"Using QA Token: {QA_TOKEN[:10]}...")
# --- API Logic ---
def handle_batch_scan():
    """
    UI: Manages the progress bar, updates the app state, and processes data.
    """
    input_df = st.session_state.get("df_input")
    
    # 1. Validation
    if input_df is None or input_df.empty:
        st.warning("No data found in the table.")
        return

    order_ids = input_df["Order ID"].dropna().str.strip().tolist()
    order_ids = [idx for idx in order_ids if idx]
    if not order_ids:
        st.warning("No valid Order IDs to scan.")
        return

    # 2. Setup UI Elements
    progress_bar = st.progress(0)
    status_text = st.empty()
    scan_log = []
    total = len(order_ids)
    start_time = time.time()

    # 3. Run Generator and Update UI
    for i, res in enumerate(run_parallel_scan_generator(order_ids)):
        order_id = res.get("Order ID")
        success = res.get("status") == "success"
        msg = res.get("msg") or res.get("tracking") 
        carrier_name = res.get("carrier", "")

        # Update the table in memory only if successful AND is USPS
        # (Merged the logic you had down in the button into this generator loop)
        if success and "USPS" in str(carrier_name):
            st.session_state.df_input.loc[
                st.session_state.df_input["Order ID"] == order_id, "Tracking Number"
            ] = msg
            print(f"Updated Order {order_id} with USPS Tracking: {msg}")
            
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

    # 4. Finalize
    duration = time.time() - start_time
    st.session_state.scan_results_summary = pd.DataFrame(scan_log)
    status_text.success(f"Batch scan complete! {total} orders in {duration:.2f}s")
    
    # Trigger a single rerun to refresh the UI with the new tracking numbers
    st.rerun()

def scanID(order_no):
    url = "https://pod-api.sdspod.com/pod/qc/factoryOrder/fast?"
    timestamp_ms = int(time.time() * 1000)

    headers = {
        "User-Agent": "Mozilla/5.0...",
        "Accept": "application/json, text/plain, */*",
        "access-token": QA_TOKEN,
    }

    params = {"no": order_no, "t": timestamp_ms}
    try:

        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
        pass
    except Exception as e:
        return {"status": "error", "msg": str(e)}
    return None

# --- Streamlit UI ---
def render_SDS_widgets():
    st.divider()
    st.markdown("### 🛠️ SDS 忆点万象 订单操作")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔍 获取待排产订单", use_container_width=True):
            with st.spinner("Fetching from SDS..."):
                ids = factory_fetch_records()
                if ids:
                    st.session_state.df_input = pd.DataFrame({
                        "Order ID": ids, 
                        "Tracking Number": [""] * len(ids)
                    })
                    st.success(f"Loaded {len(ids)} orders.")
                    st.rerun()

    with col2:
        # The button now simply calls the function which handles UI & state
        if st.button("🚀 执行批量 面单获取", type="primary", use_container_width=True):
            handle_batch_scan()

    # --- Optional: Display Summary below if it exists ---
    if "scan_results_summary" in st.session_state:
        with st.expander("📄 查看最近一次扫描详情", expanded=False):
            st.dataframe(st.session_state.scan_results_summary, use_container_width=True)