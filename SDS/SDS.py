import streamlit as st
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor
from SDS.QA_scan import get_headers as get_qa_scan_headers, scanID
from SDS.factoryFetch import factory_fetch_records
from SDS.platform_selector import render_platform_dropdown
from SDS.pre_scan import DEFAULT_MAX_WORKERS, run_parallel_scan_generator
from SDS.scan_workflow import build_scan_log_row
from SDS.unproducedFetch import fetch_unproduced_orders_with_tracking
from usps_batch_ui import render_usps_batch_tables

DEFAULT_QUEUE_TITLE = "待扫描队列"
SDS_TABLE_HEIGHT = 720


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
def handle_batch_scan(order_ids, max_workers=DEFAULT_MAX_WORKERS):
    """
    UI: Manages the progress bar and processes data.
    Takes a local list of order_ids passed directly from the UI trigger.
    """
    if not order_ids:
        st.warning("No valid Order IDs to scan.")
        return

    clean_order_ids = [str(order_id).strip() for order_id in order_ids if str(order_id).strip()]
    if not clean_order_ids:
        st.warning("No valid Order IDs to scan.")
        return

    # 1. Setup UI Elements
    progress_bar = st.progress(0)
    status_text = st.empty()
    scan_log = []
    total = len(clean_order_ids)
    start_time = time.time()
    qa_headers = get_qa_scan_headers()
    label_scan_workers = min(max_workers, len(clean_order_ids))
    label_scan_executor = ThreadPoolExecutor(max_workers=label_scan_workers)
    label_scan_futures = {
        order_id: label_scan_executor.submit(scanID, order_id, qa_headers)
        for order_id in clean_order_ids
    }

    # 2. Run Generator and Update UI
    for i, res in enumerate(run_parallel_scan_generator(clean_order_ids, max_workers=max_workers)):
        order_id = str(res.get("Order ID", "")).strip()
        label_future = label_scan_futures.get(order_id)
        label_scan_result = label_future.result() if label_future else None
        scan_log.append(build_scan_log_row(res, label_scan_result=label_scan_result))

        # Update progress
        queried = i + 1
        remaining = total - queried
        percent_complete = queried / total
        progress_bar.progress(percent_complete)
        status_text.text(
            f"Queried {queried}/{total} | Left {remaining} | Current: {res.get('Order ID')}"
        )

    label_scan_executor.shutdown(wait=True)

    # 3. Finalize
    duration = time.time() - start_time
    scan_results_df = pd.DataFrame(scan_log)
    st.session_state.scan_results_summary = scan_results_df
    status_text.success(f"Batch scan complete! {total} orders in {duration:.2f}s")
    
    st.rerun()

# --- Streamlit UI ---
def render_SDS_widgets():
    st.divider()
   
    # st.markdown("### 🛠️ SDS 3D 热转印 订单操作")
    render_platform_dropdown()  # Platform selector at the top of the section
    init_sds_state()
    max_workers = st.slider(
        "Tracking query concurrency",
        min_value=10,
        max_value=150,
        value=DEFAULT_MAX_WORKERS,
        step=10
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📦 获取未排产订单", use_container_width=True):
            with st.spinner("Fetching unproduced orders from SDS..."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_tracking_progress(queried, total, result):
                    remaining = total - queried
                    progress_bar.progress(queried / total if total else 0)
                    status_text.text(
                        f"Queried {queried}/{total} | Left {remaining} | Current: {result.get('Order ID')}"
                    )

                local_fetched_ids, display_rows = fetch_unproduced_orders_with_tracking(
                    max_workers=max_workers,
                    on_progress=update_tracking_progress
                )
                progress_bar.empty()
                status_text.empty()

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
        
        if st.button("🚀 执行批量 出面单", type="primary", use_container_width=True, disabled=button_disabled):
            local_scan_list = list(current_orders)
            clear_order_queue()
            handle_batch_scan(local_scan_list, max_workers=max_workers)

    # --- Display Fetched Orders First ---
    # If there are fetched IDs in our temporary holding list, show them cleanly here
    if st.session_state.fetched_ids_list:
        st.markdown(f"📋 **{st.session_state.fetched_orders_title} ({len(st.session_state.fetched_ids_list)} 个订单):**")
        
        render_order_queue()
        if st.session_state.fetched_orders_display:
            render_usps_batch_tables(
                pd.DataFrame(st.session_state.fetched_orders_display),
                key_prefix="sds_queue",
                expanded=True,
                table_height=SDS_TABLE_HEIGHT
            )

    # --- Summary Display Panel ---
    if "scan_results_summary" in st.session_state:
        with st.expander("📄 查看最近一次扫描详情", expanded=True):
            st.dataframe(
                sort_usps_first(st.session_state.scan_results_summary),
                use_container_width=True,
                height=SDS_TABLE_HEIGHT
            )
        render_usps_batch_tables(
            st.session_state.scan_results_summary,
            key_prefix="sds_scan",
            expanded=True,
            table_height=SDS_TABLE_HEIGHT
        )


def render_order_queue():
    display_rows = st.session_state.fetched_orders_display
    display_df = pd.DataFrame(display_rows) if display_rows else pd.DataFrame({
        "Order ID": st.session_state.fetched_ids_list
    })
    display_df = sort_usps_first(display_df)
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=SDS_TABLE_HEIGHT
    )


def sort_usps_first(df):
    if "Carrier" not in df.columns:
        return sort_by_tracking_number(df)

    sorted_df = df.copy()
    sorted_df["_usps_first"] = ~sorted_df["Carrier"].fillna("").astype(str).str.upper().str.contains("USPS", na=False)
    sort_columns = ["_usps_first"]
    if "Tracking Number" in sorted_df.columns:
        sorted_df["_tracking_sort"] = sorted_df["Tracking Number"].fillna("").astype(str)
        sort_columns.append("_tracking_sort")

    sorted_df = sorted_df.sort_values(by=sort_columns)
    sorted_df = sorted_df.drop(columns=[col for col in ["_usps_first", "_tracking_sort"] if col in sorted_df.columns])
    return sorted_df


def sort_by_tracking_number(df):
    if "Tracking Number" not in df.columns:
        return df

    sorted_df = df.copy()
    sorted_df["_tracking_sort"] = sorted_df["Tracking Number"].fillna("").astype(str)
    sorted_df = sorted_df.sort_values(by=["_tracking_sort"]).drop(columns=["_tracking_sort"])
    return sorted_df
