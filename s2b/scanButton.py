import streamlit as st
import time
# Ensure the path to scan.py is correct based on your folder structure
from S2B.scan import push_delivery_print

def render_scan_buttons(order_ids=None):
    """
    Renders the tracking and S2B scan buttons.
    Accepts a list of order_ids to process.
    """
    col1, col2 = st.columns(2)


    with col2:
        if st.button("S2B UV Scan", use_container_width=True):
            if not order_ids:
                st.warning("No Order IDs available to scan.")
                return None

            # If order_ids is a single string, convert to list for consistency
            ids_to_scan = [order_ids] if isinstance(order_ids, str) else order_ids
            
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, order_id in enumerate(ids_to_scan):
                status_text.text(f"Processing ({i+1}/{len(ids_to_scan)}): {order_id}")
                result = push_delivery_print(order_id)
                if result and result.get("status_code") == 200:
                    st.toast(f"✅ {order_id} pushed", icon="🚀")
                else:
                    # Extract the specific error message from the API (e.g., "非本工厂订单")
                    error_msg = result.get("msg", "Unknown Error")
                    st.error(f"❌ {order_id}: {error_msg}")
                
                # Update progress bar
                progress_bar.progress((i + 1) / len(ids_to_scan))
            
            st.success(f"Batch scan complete for {len(ids_to_scan)} orders.")
            return "s2b_complete"
            
    return None