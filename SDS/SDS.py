import streamlit as st
import pandas as pd
import time
from SDS.factoryFetch import factory_fetch_records
from SDS.platform_selector import render_platform_dropdown
from SDS.pre_scan import run_parallel_scan_generator
from SDS.scan_workflow import build_scan_log_row
from SDS.unproducedFetch import fetch_unproduced_orders_with_tracking

DEFAULT_QUEUE_TITLE = "待扫描队列"


def init_sds_state():
    st.session_state.setdefault("fetched_ids_list", [])
    st.session_state.setdefault("fetched_orders_display", [])
    st.session_state.setdefault("fetched_orders_title", DEFAULT_QUEUE_TITLE)


def set_order_queue(order_ids, title, display_rows=None):
    st.session_state.fetched_ids_list = order_ids
    st.session_state.fetched_orders_display = display_rows or []
    st.session_state.fetched_orders_title = title


def clear_order_queue():
    set_order_queue([], DEFAULT_QUEUE_TITLE)


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
        scan_log.append(build_scan_log_row(res))

        # Update progress
        percent_complete = (i + 1) / total
        progress_bar.progress(percent_complete)
        status_text.text(f"Processing {i+1}/{total}: {res.get('Order ID')}")

    # 3. Finalize
    duration = time.time() - start_time
    st.session_state.scan_results_summary = pd.DataFrame(scan_log)
    status_text.success(f"Batch scan complete! {total} orders in {duration:.2f}s")
    
    st.rerun()

# --- Streamlit UI ---
def render_SDS_widgets():
    st.divider()
   
    # st.markdown("### 🛠️ SDS 3D 热转印 订单操作")
    render_platform_dropdown()  # Platform selector at the top of the section
    init_sds_state()

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📦 获取未排产订单", use_container_width=True):
            with st.spinner("Fetching unproduced orders from SDS..."):
                local_fetched_ids, display_rows = fetch_unproduced_orders_with_tracking()

                if local_fetched_ids:
                    set_order_queue(local_fetched_ids, "未排产订单", display_rows)
                    st.success(f"Successfully loaded {len(local_fetched_ids)} unproduced orders.")
                else:
                    set_order_queue([], "未排产订单")
                    st.warning("No unproduced orders found.")

    with col2:
        if st.button("🔍 获取生产中订单", use_container_width=True):
            with st.spinner("Fetching from SDS..."):
                local_fetched_ids = factory_fetch_records()
                
                if local_fetched_ids:
                    set_order_queue(local_fetched_ids, "生产中订单")
                    st.success(f"Successfully loaded {len(local_fetched_ids)} orders.")
                else:
                    set_order_queue([], "生产中订单")
                    st.warning("No orders found.")

    with col3:
        current_orders = st.session_state.fetched_ids_list
        button_disabled = len(current_orders) == 0
        
        if st.button("🚀 执行批量 面单获取", type="primary", use_container_width=True, disabled=button_disabled):
            local_scan_list = list(current_orders)
            clear_order_queue()
            handle_batch_scan(local_scan_list)

    # --- Display Fetched Orders First ---
    # If there are fetched IDs in our temporary holding list, show them cleanly here
    if st.session_state.fetched_ids_list:
        st.markdown(f"📋 **{st.session_state.fetched_orders_title} ({len(st.session_state.fetched_ids_list)} 个订单):**")
        
        render_order_queue()

    # --- Summary Display Panel ---
    if "scan_results_summary" in st.session_state:
        with st.expander("📄 查看最近一次扫描详情", expanded=True):
            st.dataframe(st.session_state.scan_results_summary, use_container_width=True)


def render_order_queue():
    display_rows = st.session_state.fetched_orders_display
    display_df = pd.DataFrame(display_rows) if display_rows else pd.DataFrame({
        "Order ID": st.session_state.fetched_ids_list
    })
    st.dataframe(display_df, use_container_width=True, hide_index=True)
