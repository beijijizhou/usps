import streamlit as st
from s2b.scan import push_delivery_print, TOKENS

def render_scan_buttons(order_ids=None):
    col1, col2 = st.columns(2)

    with col1:
        if st.button("S2B UV Scan", use_container_width=True, type="primary"):
            run_batch_process(order_ids, "UV Scan", TOKENS["UV"])

    with col2:
        if st.button("S2B T-Shirt Scan", use_container_width=True):
            run_batch_process(order_ids, "T-Shirt Scan", TOKENS["T-Shirt"])

def run_batch_process(order_ids, label, token):
    if not order_ids:
        st.warning(f"No Order IDs available for {label}.")
        return

    ids_to_scan = [order_ids] if isinstance(order_ids, str) else order_ids
    progress_bar = st.progress(0)
    
    for i, order_id in enumerate(ids_to_scan):
        try:
            # Pass the specific token here
            result = push_delivery_print(order_id, token)
            
            if result and result.get("status_code") == 200:
                st.toast(f"✅ {order_id} ({label}) pushed", icon="🚀")
            else:
                st.error(f"❌ {order_id} failed (Check Token/ID)")
                
        except Exception as e:
            st.error(f"Error: {e}")
        
        progress_bar.progress((i + 1) / len(ids_to_scan))
    
    st.success(f"{label} Complete!")