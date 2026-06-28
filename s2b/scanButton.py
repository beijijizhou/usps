import streamlit as st
from s2b.scan import push_delivery_print, TOKENS

from concurrent.futures import ThreadPoolExecutor, as_completed

def render_scan_buttons(order_ids=None):
    # Created 3 columns to fit the new button
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("S2B UV Scan", width='stretch', type="primary"):
            run_batch_process(order_ids, "UV Scan", TOKENS["UV"])

    with col2:
        if st.button("S2B T-Shirt Scan", width='stretch'):
            run_batch_process(order_ids, "T-Shirt Scan", TOKENS["T-Shirt"])

    with col3:
        if st.button("S2B 3D Scan", width='stretch'):
            # Assumes TOKENS["3D"] exists; adjust the key if your dictionary uses a different name
            run_batch_process(order_ids, "3D Scan", TOKENS["3D"])



def process_single_order(order_id, token, label):
    """
    Worker function executed in parallel. 
    Returns a tuple of (order_id, success_status, error_message)
    """
    try:
        result = push_delivery_print(order_id, token)
        if result and result.get("status_code") == 200:
            return order_id, True, None
        else:
            return order_id, False, "Check Token/ID"
    except Exception as e:
        return order_id, False, str(e)


def run_batch_process(order_ids, label, token, max_workers=5):
    if not order_ids:
        st.warning(f"No Order IDs available for {label}.")
        return

    ids_to_scan = [order_ids] if isinstance(order_ids, str) else order_ids
    total_orders = len(ids_to_scan)
    
    progress_bar = st.progress(0)
    status_text = st.empty() # Placeholder to show current progress count

    # Use ThreadPoolExecutor for parallel execution
    # adjust max_workers based on your API's rate limits
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks to the thread pool
        futures = {
            executor.submit(process_single_order, order_id, token, label): order_id 
            for order_id in ids_to_scan
        }
        
        # Process results as they complete on the main thread
        for i, future in enumerate(as_completed(futures)):
            order_id, success, error_msg = future.result()
            
            # UI Updates are safe here because we are back on the main thread
            if success:
                st.toast(f"✅ {order_id} ({label}) pushed", icon="🚀")
            else:
                st.error(f"❌ {order_id} failed: {error_msg}")
                
            # Update progress bar and text dynamically
            completion_percentage = (i + 1) / total_orders
            progress_bar.progress(completion_percentage)
            status_text.text(f"Processed {i + 1}/{total_orders} items...")

    # Clean up the temporary status text and show final message
    status_text.empty()
    st.success(f"{label} Complete!")
