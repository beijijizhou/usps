import streamlit as st
import time
from SDS.factoryFetch import factory_fetch_records  # Your SDS 3 fetch logic
from SDS.QA_scan import scanID                   # Your QC scan logic

def render_sds3_widgets():
    """
    Renders the SDS 3 Fetching and QC Scanning interface.
    """
    st.markdown("### 🛠️ SDS 3 Operations")

    # 1. The Fetch Button
    if st.button("🔍 Fetch SDS 3 Records", use_container_width=True):
        with st.spinner("Connecting to SDS 3 Factory API..."):
            # This calls the function from your sds_fetch.py
            ids = factory_fetch_records()
            
            if ids:
                st.session_state.sds3_order_list = ids
                st.success(f"SDS 3: Found {len(ids)} records.")
            else:
                st.error("SDS 3 Error: No records found. Please check your Token/Cookie.")

    st.divider()

    # 2. The Batch Scan Button
    # Only enabled if there are IDs in the list
    if "sds3_order_list" in st.session_state and st.session_state.sds3_order_list:
        order_ids = st.session_state.sds3_order_list
        st.info(f"Currently holding **{len(order_ids)}** IDs from SDS 3.")

        if st.button("🚀 Run SDS 3 QC Batch Scan", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results_log = []
            
            for i, order_no in enumerate(order_ids):
                status_text.text(f"Scanning SDS 3 Order ({i+1}/{len(order_ids)}): {order_no}")
                
                # Call the scanID function
                response = scanID(order_no)
                
                # Check for success in the response
                if response and response.get("status") == "success":
                    results_log.append(f"✅ {order_no}: Success")
                else:
                    msg = response.get("msg", "Scan Failed") if response else "No Response"
                    results_log.append(f"❌ {order_no}: {msg}")
                    st.warning(f"Issue with {order_no}: {msg}")
                
                # Update progress
                progress_bar.progress((i + 1) / len(order_ids))
                time.sleep(0.05) # Prevent overwhelming the API

            st.success("SDS 3 Batch Scan Complete!")
            
            # Show a summary in an expander
            with st.expander("View Full Scan Log"):
                for entry in results_log:
                    st.write(entry)
    else:
        st.caption("Fetch records first to enable the SDS 3 Batch Scan.")