import streamlit as st
import pandas as pd
import time
from datetime import date
from concurrent.futures import ThreadPoolExecutor
from SDS.QA_scan import get_headers as get_qa_scan_headers, scanID
from SDS.factoryFetch import factory_fetch_records
from SDS.platform_selector import render_platform_dropdown
from SDS.pre_scan import DEFAULT_MAX_WORKERS, run_parallel_scan_generator
from SDS.producedTrackingFetch import fetch_produced_tracking_since
from SDS.scan_workflow import build_scan_log_row
from SDS.unproducedFetch import fetch_old_unfinished_orders_with_tracking, fetch_unproduced_orders_with_tracking
from usps_batch_ui import render_usps_batch_tables

DEFAULT_QUEUE_TITLE = "待扫描队列"
SDS_TABLE_HEIGHT = 720
DISPLAY_COLUMN_LABELS = {
    "Order ID": "订单号",
    "Tracking Number": "物流单号",
    "Merchant Order No": "销售订单号",
    "Carrier": "渠道",
    "Factory Status": "工厂状态",
    "Begin Time": "开始时间",
    "Finished Time": "完成时间",
    "Ship Time": "发货时间",
    "Status": "状态",
    "Label Scan": "出面单",
    "Label Scan Detail": "出面单接口详情",
    "Label PDF": "面单PDF",
    "Scan Status": "扫描状态",
    "Result": "结果",
}


def init_sds_state():
    st.session_state.setdefault("fetched_ids_list", [])
    st.session_state.setdefault("fetched_orders_display", [])
    st.session_state.setdefault("fetched_orders_title", DEFAULT_QUEUE_TITLE)
    st.session_state.setdefault("fetched_orders_can_scan", False)


def set_order_queue(order_ids, title, display_rows=None, can_scan=False):
    st.session_state.fetched_ids_list = order_ids
    st.session_state.fetched_orders_display = display_rows or []
    st.session_state.fetched_orders_title = title
    st.session_state.fetched_orders_can_scan = can_scan


def clear_order_queue():
    set_order_queue([], DEFAULT_QUEUE_TITLE)


def render_tracking_fetch_progress(selected_platform, fetch_func, success_title, empty_title, can_scan, max_workers):
    with st.spinner(f"正在从 {selected_platform} 获取{success_title}..."):
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_tracking_progress(queried, total, result):
            remaining = total - queried
            progress_bar.progress(queried / total if total else 0)
            status_text.text(
                f"已查询 {queried}/{total} | 剩余 {remaining} | 当前订单：{result.get('Order ID')}"
            )

        start_time = time.time()
        local_fetched_ids, display_rows = fetch_func(
            max_workers=max_workers,
            on_progress=update_tracking_progress
        )
        duration = time.time() - start_time
        progress_bar.empty()
        status_text.empty()

        if local_fetched_ids:
            set_order_queue(local_fetched_ids, success_title,
                            display_rows, can_scan=can_scan)
            st.success(
                f"已从 {selected_platform} 成功加载 {len(local_fetched_ids)} 个{success_title}，用时 {duration:.2f} 秒。"
            )
        else:
            set_order_queue([], empty_title, can_scan=can_scan)
            st.warning(f"没有找到{empty_title}。")


# --- API Logic ---
def handle_batch_scan(order_ids, max_workers=DEFAULT_MAX_WORKERS):
    """
    UI: Manages the progress bar and processes data.
    Takes a local list of order_ids passed directly from the UI trigger.
    """
    if not order_ids:
        st.warning("没有可处理的订单号。")
        return

    clean_order_ids = [str(order_id).strip()
                       for order_id in order_ids if str(order_id).strip()]
    if not clean_order_ids:
        st.warning("没有可处理的订单号。")
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
        scan_log.append(build_scan_log_row(
            res, label_scan_result=label_scan_result))

        # Update progress
        queried = i + 1
        remaining = total - queried
        percent_complete = queried / total
        progress_bar.progress(percent_complete)
        status_text.text(
            f"已查询 {queried}/{total} | 剩余 {remaining} | 当前订单：{res.get('Order ID')}"
        )

    label_scan_executor.shutdown(wait=True)

    # 3. Finalize
    duration = time.time() - start_time
    scan_results_df = pd.DataFrame(scan_log)
    st.session_state.scan_results_summary = scan_results_df
    status_text.success(f"批量出面单完成！共 {total} 个订单，用时 {duration:.2f} 秒")

    st.rerun()

# --- Streamlit UI ---


def render_SDS_widgets():
    st.divider()

    # st.markdown("### 🛠️ SDS 3D 热转印 订单操作")
    # Platform selector at the top of the section
    selected_platform = render_platform_dropdown()
    init_sds_state()
    max_workers = st.slider(
        "物流单号查询并发数",
        min_value=10,
        max_value=1500,
        value=DEFAULT_MAX_WORKERS,
        step=10
    )

    old_days_before = st.number_input(
        "历史订单查询天数",
        min_value=2,
        max_value=30,
        value=7,
        step=1,
        help="用于查询昨天之前、仍处于生产中的未完成订单。"
    )

    history_col1, history_col2 = st.columns(2)
    with history_col1:
        produced_start_date = st.date_input(
            "已生产物流单号开始日期",
            value=date(date.today().year, 5, 1),
            help="用于从指定日期开始查询所有已生产/已完成订单的 tracking number。"
        )
    with history_col2:
        produced_end_date = st.date_input(
            "已生产物流单号结束日期",
            value=date.today()
        )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📦 获取未排产订单", use_container_width=True):
            render_tracking_fetch_progress(
                selected_platform=selected_platform,
                fetch_func=fetch_unproduced_orders_with_tracking,
                success_title="未排产订单",
                empty_title="未排产订单",
                can_scan=False,
                max_workers=max_workers
            )

    with col2:
        if st.button("🗓️ 获取昨天之前生产中订单", use_container_width=True):
            render_tracking_fetch_progress(
                selected_platform=selected_platform,
                fetch_func=lambda max_workers, on_progress: fetch_old_unfinished_orders_with_tracking(
                    days_before=old_days_before,
                    max_workers=max_workers,
                    on_progress=on_progress
                ),
                success_title="昨天之前生产中未完成订单",
                empty_title="昨天之前生产中未完成订单",
                can_scan=True,
                max_workers=max_workers
            )

    with col3:
        if st.button("🔍 获取生产中订单", use_container_width=True):
            with st.spinner(f"正在从 {selected_platform} 获取订单..."):
                start_time = time.time()
                local_fetched_ids = factory_fetch_records()
                duration = time.time() - start_time

                if local_fetched_ids:
                    set_order_queue(local_fetched_ids, "生产中订单", can_scan=True)
                    st.success(
                        f"已从 {selected_platform} 成功加载 {len(local_fetched_ids)} 个订单，用时 {duration:.2f} 秒。")
                else:
                    set_order_queue([], "生产中订单", can_scan=True)
                    st.warning("没有找到订单。")

    with col4:
        if st.button("📊 查询已生产物流单号", use_container_width=True):
            render_tracking_fetch_progress(
                selected_platform=selected_platform,
                fetch_func=lambda max_workers, on_progress: fetch_produced_tracking_since(
                    start_date=produced_start_date,
                    end_date=produced_end_date,
                    max_workers=max_workers,
                    on_progress=on_progress
                ),
                success_title="已生产物流单号记录",
                empty_title="已生产物流单号记录",
                can_scan=False,
                max_workers=max_workers
            )

    current_orders = st.session_state.fetched_ids_list
    button_disabled = len(
        current_orders) == 0 or not st.session_state.fetched_orders_can_scan
    scan_col, _ = st.columns([1, 3])
    with scan_col:

        if st.button("🚀 执行批量 出面单", type="primary", use_container_width=True, disabled=button_disabled):
            local_scan_list = list(current_orders)
            clear_order_queue()
            handle_batch_scan(local_scan_list, max_workers=max_workers)

    # --- Display Fetched Orders First ---
    # If there are fetched IDs in our temporary holding list, show them cleanly here
    if st.session_state.fetched_ids_list:
        st.markdown(
            f"📋 **{st.session_state.fetched_orders_title} ({len(st.session_state.fetched_ids_list)} 个订单):**")
        if not st.session_state.fetched_orders_can_scan:
            st.info("当前列表用于预览/导出物流单号，不会执行出面单。只有生产中订单列表才能出面单。")

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
            summary_df = localize_dataframe(sort_usps_first(
                st.session_state.scan_results_summary))
            st.dataframe(
                summary_df,
                use_container_width=True,
                height=SDS_TABLE_HEIGHT,
                column_config={
                    "面单PDF": st.column_config.LinkColumn("面单PDF", display_text="打开面单")
                }
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
    localized_df = localize_dataframe(display_df)
    st.dataframe(
        localized_df,
        use_container_width=True,
        hide_index=True,
        height=SDS_TABLE_HEIGHT
    )
    st.download_button(
        "⬇️ 下载当前列表 CSV",
        data=localized_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{st.session_state.fetched_orders_title}.csv",
        mime="text/csv",
        use_container_width=True
    )


def localize_dataframe(df):
    return df.rename(columns={key: value for key, value in DISPLAY_COLUMN_LABELS.items() if key in df.columns})


def sort_usps_first(df):
    if "Carrier" not in df.columns:
        return sort_by_tracking_number(df)

    sorted_df = df.copy()
    sorted_df["_usps_first"] = ~sorted_df["Carrier"].fillna(
        "").astype(str).str.upper().str.contains("USPS", na=False)
    sort_columns = ["_usps_first"]
    if "Tracking Number" in sorted_df.columns:
        sorted_df["_tracking_sort"] = sorted_df["Tracking Number"].fillna(
            "").astype(str)
        sort_columns.append("_tracking_sort")

    sorted_df = sorted_df.sort_values(by=sort_columns)
    sorted_df = sorted_df.drop(columns=[col for col in [
                               "_usps_first", "_tracking_sort"] if col in sorted_df.columns])
    return sorted_df


def sort_by_tracking_number(df):
    if "Tracking Number" not in df.columns:
        return df

    sorted_df = df.copy()
    sorted_df["_tracking_sort"] = sorted_df["Tracking Number"].fillna(
        "").astype(str)
    sorted_df = sorted_df.sort_values(
        by=["_tracking_sort"]).drop(columns=["_tracking_sort"])
    return sorted_df
