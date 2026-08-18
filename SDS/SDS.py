import streamlit as st
import pandas as pd
import time
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
from SDS.QA_scan import get_headers as get_qa_scan_headers, get_qc_order_info, scanID
from SDS.factoryFetch import factory_fetch_records
from SDS.platform_selector import render_platform_dropdown
from SDS.pre_scan import DEFAULT_MAX_WORKERS, process_single_order
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
    "Same Order Count": "同单件数",
    "Item Quantity": "单项数量",
    "Carrier": "渠道",
    "Factory Status": "工厂状态",
    "Begin Time": "开始时间",
    "Finished Time": "完成时间",
    "Ship Time": "发货时间",
    "Status": "状态",
    "Label Scan": "质检",
    "Label Scan Detail": "质检接口详情",
    "Label Scan Raw": "质检接口原始返回",
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
def handle_batch_scan(order_ids, max_workers=DEFAULT_MAX_WORKERS, display_rows=None):
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

    progress_bar = st.progress(0)
    status_text = st.empty()
    scan_log = []
    total = len(clean_order_ids)
    start_time = time.time()
    qa_headers = get_qa_scan_headers()
    order_groups = build_order_scan_groups(clean_order_ids, display_rows=display_rows)
    completed = 0
    group_worker_count = min(max_workers, len(order_groups)) if order_groups else 1

    with ThreadPoolExecutor(max_workers=group_worker_count) as executor:
        futures = {
            executor.submit(scan_order_group, group_order_ids, qa_headers): group_key
            for group_key, group_order_ids in order_groups
        }
        for future in as_completed(futures):
            group_rows = future.result()
            scan_log.extend(group_rows)
            completed += len(group_rows)
            remaining = total - completed
            progress_bar.progress(completed / total if total else 0)
            status_text.text(
                f"已质检/查询 {completed}/{total} | 剩余 {remaining} | 当前组：{futures[future]}"
            )

    duration = time.time() - start_time
    scan_results_df = pd.DataFrame(scan_log)
    st.session_state.scan_results_summary = scan_results_df
    status_text.success(f"批量质检并查询面单完成！共 {total} 个订单，用时 {duration:.2f} 秒")

    st.rerun()


def build_order_scan_groups(order_ids, display_rows=None):
    display_rows = display_rows if display_rows is not None else st.session_state.get("fetched_orders_display", [])
    merchant_by_order_id = {
        str(row.get("Order ID", "")).strip(): str(row.get("Merchant Order No", "")).strip()
        for row in display_rows
        if str(row.get("Order ID", "")).strip()
    }

    grouped = {}
    ungrouped_order_ids = []
    for order_id in order_ids:
        group_key = merchant_by_order_id.get(order_id)
        if group_key:
            grouped.setdefault(group_key, []).append(order_id)
        else:
            ungrouped_order_ids.append(order_id)

    groups = list(grouped.items())
    groups.extend(group_consecutive_order_ids(ungrouped_order_ids))
    return groups


def group_consecutive_order_ids(order_ids):
    sorted_ids = sort_order_ids_for_qc(order_ids)
    groups = []
    current_group = []
    previous_number = None

    for order_id in sorted_ids:
        current_number = parse_order_number(order_id)
        if (
            current_group
            and previous_number is not None
            and current_number is not None
            and current_number == previous_number + 1
        ):
            current_group.append(order_id)
        else:
            if current_group:
                groups.append(make_consecutive_group(current_group))
            current_group = [order_id]
        previous_number = current_number

    if current_group:
        groups.append(make_consecutive_group(current_group))
    return groups


def make_consecutive_group(order_ids):
    if len(order_ids) == 1:
        return order_ids[0], order_ids
    return f"连续生产单 {order_ids[0]} - {order_ids[-1]}", order_ids


def parse_order_number(order_id):
    value = str(order_id).strip()
    return int(value) if value.isdigit() else None


def scan_order_group(order_ids, qa_headers):
    rows = []
    sorted_order_ids = sort_order_ids_for_qc(order_ids)
    order_info = None
    batch_reason = ""

    if len(sorted_order_ids) == 1:
        lookup_order_id = sorted_order_ids[0]
        order_info = fetch_qc_order_info_safely(lookup_order_id, qa_headers)
        factory_order_ids = get_factory_order_ids(order_info)
        if factory_order_ids:
            sorted_order_ids = sort_order_ids_for_qc(factory_order_ids)

    qc_results = {}

    if len(sorted_order_ids) > 1:
        batch_qc_result = scanID(sorted_order_ids[0], qa_headers, batch=True)
        for order_id in sorted_order_ids:
            qc_results[order_id] = build_group_qc_result(order_id, batch_qc_result, sorted_order_ids)
    else:
        order_id = sorted_order_ids[0]
        if order_info is None:
            order_info = fetch_qc_order_info_safely(order_id, qa_headers)
        use_batch_qc, batch_reason = order_info_needs_batch_qc(order_info)
        qc_result = scanID(order_id, qa_headers, batch=use_batch_qc)
        if use_batch_qc and qc_result.get("ok"):
            qc_result["message"] = f"{batch_reason}，批量质检完成"
        elif batch_reason and not qc_result.get("message"):
            qc_result["message"] = batch_reason
        qc_results[order_id] = qc_result

    for order_id in sorted_order_ids:
        scan_result = wait_for_tracking_after_group_qc(order_id, qa_headers)
        rows.append(build_scan_log_row(scan_result, label_scan_result=qc_results.get(order_id)))
    return rows


def fetch_qc_order_info_safely(order_id, qa_headers):
    try:
        return get_qc_order_info(order_id, headers=qa_headers)
    except Exception:
        return None


def get_factory_order_ids(order_info):
    if not order_info:
        return []
    return [
        str(factory_order.get("factoryOrderNo", "")).strip()
        for factory_order in order_info.get("factoryOrderList", [])
        if str(factory_order.get("factoryOrderNo", "")).strip()
    ]


def order_info_needs_batch_qc(order_info):
    if not order_info:
        return False, "质检前详情查询失败，使用普通质检"

    factory_orders = order_info.get("factoryOrderList") or []
    if len(factory_orders) > 1:
        return True, f"同销售订单包含 {len(factory_orders)} 个生产单"

    for factory_order in factory_orders:
        quantity = factory_order.get("currentQcQty") or factory_order.get("qty") or 0
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            quantity = 0
        if quantity > 1:
            return True, f"单项多件，待质检数量 {quantity}"

    return False, "单件普通质检"


def build_group_qc_result(order_id, batch_qc_result, group_order_ids):
    result = dict(batch_qc_result or {})
    result["order_no"] = order_id
    if result.get("ok"):
        result["message"] = f"同销售订单批量质检完成，共 {len(group_order_ids)} 个生产单"
    return result


def sort_order_ids_for_qc(order_ids):
    def sort_key(order_id):
        value = str(order_id)
        digits = "".join(char for char in value if char.isdigit())
        return (digits.zfill(32), value)

    return sorted(order_ids, key=sort_key)


def wait_for_tracking_after_group_qc(order_id, qa_headers, attempts=4, delay_seconds=1.5):
    result = None
    for attempt in range(attempts):
        result = process_single_order(order_id, qa_headers)
        if result.get("status") == "success" and result.get("tracking"):
            return result
        if attempt < attempts - 1:
            time.sleep(delay_seconds)
    return result or {
        "Order ID": order_id,
        "status": "error",
        "msg": "质检后仍未查到物流单号",
    }

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
        "今天以前生产中订单查询天数",
        min_value=1,
        max_value=30,
        value=7,
        step=1,
        help="查询从 N 天前 00:00:00 到昨天 23:59:59，仍处于生产中的订单。"
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
        if st.button("🗓️ 获取今天以前生产中订单", use_container_width=True):
            render_tracking_fetch_progress(
                selected_platform=selected_platform,
                fetch_func=lambda max_workers, on_progress: fetch_old_unfinished_orders_with_tracking(
                    days_before=old_days_before,
                    max_workers=max_workers,
                    on_progress=on_progress
                ),
                success_title="今天以前生产中订单",
                empty_title="今天以前生产中订单",
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

        if st.button("🚀 执行批量质检并查询面单", type="primary", use_container_width=True, disabled=button_disabled):
            local_scan_list = list(current_orders)
            local_display_rows = list(st.session_state.get("fetched_orders_display", []))
            clear_order_queue()
            handle_batch_scan(local_scan_list, max_workers=max_workers, display_rows=local_display_rows)

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
