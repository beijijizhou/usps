import streamlit as st
import pandas as pd
import requests
import time

from SDS.pre_scan import get_factory_order_id, get_tracking_from_factory_id, run_batch_pre_scan

QA_token = "sds-pod:b07b0f28-8c71-4e7c-bee1-8fcf08137a07"
factory_order_id = get_factory_order_id(2006820000273575)
print(get_tracking_from_factory_id(factory_order_id))
# --- API Logic ---
def scanID(order_no):
    url = "https://pod-api.sdspod.com/pod/qc/factoryOrder/fast?"   
    timestamp_ms = int(time.time() * 1000)
    
    # Ensure headers include your token/cookie correctly
    headers = {
        "User-Agent": "Mozilla/5.0...",
        "Accept": "application/json, text/plain, */*",
        "access-token": QA_token,
       
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
    st.markdown("### 🛠️ SDS 1号线 订单操作")

    # Column layout for the two main actions
    col1, col2 = st.columns(2)

    with col1:
        # ACTION 1: Fetch IDs into the table
        if st.button("🔍 获取待排产订单", use_container_width=True):
            from SDS.factoryFetch import factory_fetch_records 
            with st.spinner("Fetching..."):
                ids = factory_fetch_records()
                if ids:
                    st.session_state.df_input = pd.DataFrame({
                        "Order ID": ids,
                        "Tracking Number": [""] * len(ids)
                    })
                      # Test the API with the first ID to ensure it works
                    st.success(f"Injected {len(ids)} orders.")
                    st.rerun()

    with col2:
        # ACTION 2: Scan the IDs currently in the table
        if st.button("🚀 执行批量 面单获取", type="primary", use_container_width=True):
            if "df_input" in st.session_state and not st.session_state.df_input.empty:
                
                # Get the list from the current state of the editor
                order_ids = st.session_state.df_input["Order ID"].dropna().tolist()
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                scan_log = []

                for i, order_no in enumerate(order_ids):
                    if not str(order_no).strip(): continue
                    
                    status_text.text(f"Scanning {i+1}/{len(order_ids)}: {order_no}")
                    
                    # Run the API request
                    result = run_batch_pre_scan(str(order_no).strip())
                    
                    # Logic to determine success/fail based on API response structure
                    is_success = result.get("code") == 200 or result.get("status") == "success"
                    
                    scan_log.append({
                        "Order ID": order_no,
                        "Scan Status": "✅ Success" if is_success else "❌ Failed",
                        "API Message": result.get("msg", "No message") if result else "Connection Error"
                    })
                    
                    progress_bar.progress((i + 1) / len(order_ids))
                    time.sleep(0.1) # Small delay to be nice to the API

                # Show results in a clean table below
                st.session_state.scan_results_summary = pd.DataFrame(scan_log)
                status_text.success("Batch Scan Completed!")
            else:
                st.warning("No Order IDs found in the table above to scan.")

    # Display Scan Results Summary if they exist
    if "scan_results_summary" in st.session_state:
        with st.expander("📄 查看扫描结果详情", expanded=True):
            st.dataframe(st.session_state.scan_results_summary, use_container_width=True)