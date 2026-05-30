import streamlit as st
import pandas as pd
import requests
import time
from SDS.factoryFetch import factory_fetch_records

if "qa_token" not in st.session_state:
    YD_QA_TOKEN = "sds-pod:244cfc4a-4e8b-4e40-8ded-28f696b849b5"
    OTHER__QA_TOKEN = "sds-pod:38b7d608-33d6-485c-b3b0-3c5eb348e5e6"
    st.session_state.qa_token = YD_QA_TOKEN

from SDS.pre_scan import  run_parallel_scan_generator

# Assign to a local variable for shorter typing if you like
QA_TOKEN = st.session_state.qa_token
# QA_token = "sds-pod:b07b0f28-8c71-4e7c-bee1-8fcf08137a07"
# factory_order_id = get_factory_order_id(2006820000273575)
# print(get_tracking_from_factory_id(factory_order_id))
# --- API Logic ---
def handle_batch_scan():
    """
    UI: Manages the progress bar and updates the app state.
    """
    input_df = st.session_state.get("df_input")
    
    # 1. Validation
    if input_df is None or input_df.empty:
        st.warning("No data found in the table.")
        return

    order_ids = input_df["Order ID"].dropna().str.strip().tolist()
    order_ids = [idx for idx in order_ids if idx] 
    # order_ids = order_ids[:4]
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
    # This loop runs every time a thread finishes
    for i, res in enumerate(run_parallel_scan_generator(order_ids)):
        order_id = res.get("Order ID")
        success = res.get("status") == "success"
        msg = res.get("msg") or res.get("tracking") # Handle both keys

        # Update the table in memory
        if success:
            st.session_state.df_input.loc[
                st.session_state.df_input["Order ID"] == order_id, "Tracking Number"
            ] = msg
        
        scan_log.append({
            "Order ID": order_id,
            "Scan Status": "✅ Success" if success else "❌ Failed",
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
    
    # Trigger a rerun to show the new tracking numbers in the editor
    st.rerun()

def scanID(order_no):
    url = "https://pod-api.sdspod.com/pod/qc/factoryOrder/fast?"
    timestamp_ms = int(time.time() * 1000)

    # Ensure headers include your token/cookie correctly
    headers = {
        "User-Agent": "Mozilla/5.0...",
        "Accept": "application/json, text/plain, */*",
        "access-token": QA_TOKEN,

    }

    params = {"no": order_no, "t": timestamp_ms}
    print(f"Scanning Order: {order_no} with params: {params}")
    try:
        r = "1"
        # r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
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
        if st.button("🚀 执行批量 面单获取", type="primary", use_container_width=True):
            # 1. Validation
            input_df = st.session_state.get("df_input")
            if input_df is None or input_df.empty:
                st.warning("No data found in table.")
                return
            # 2. Execution
            raw_results = handle_batch_scan()

            # 3. Data Processing
            scan_log = []
            for res in raw_results:
                order_id = res["Order ID"]
                success = res["status"] == "success"
                
              
                # Update the main tracking table if successful
                if success:
                    tracking_val = res["tracking"]
                    carrier_name = res["carrier"]
                    # CHECK: Is it USPS? (Adjust the string "USPS" based on your actual API data)
                    if "USPS" in carrier_name:
                        st.session_state.df_input.loc[
                            st.session_state.df_input["Order ID"] == order_id, "Tracking Number"
                        ] = tracking_val
                        
                        scan_log.append({"Order ID": order_id,  "Tracking Number": tracking_val})
                    # else:
                    #     scan_log.append({"Order ID": order_id,  "Tracking Number": f"Other carrier: {carrier_name}"})
                else:
                    scan_log.append({"Order ID": order_id, "Tracking Number": res["msg"]})
                
                

            # 4. Feedback
            st.session_state.df_input = pd.DataFrame(scan_log)
            # st.success(f"Finished in {duration:.2f} seconds.")
            st.rerun()

    # # 5. Summary Display
    # if "scan_results_summary" in st.session_state:
    #     with st.expander("📄 查看最近一次扫描详情", expanded=False):
    #         st.dataframe(st.session_state.df_input, use_container_width=True)
    # st.rerun()