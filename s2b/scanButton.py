import streamlit as st
import pandas as pd
from s2b.scan import get_s2b_tokens, push_delivery_print

from concurrent.futures import ThreadPoolExecutor, as_completed


S2B_CHANNELS = [
    ("UV", "S2B UV 出面单"),
    ("T-Shirt", "S2B T-Shirt 出面单"),
    ("3D", "S2B 3D 出面单"),
]


def render_S2B_scan_buttons(order_ids=None, max_workers=5):
    tokens = get_s2b_tokens()
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("S2B UV 出面单", use_container_width=True, type="primary"):
            run_batch_process(order_ids, "UV", tokens.get("UV"), max_workers=max_workers)

    with col2:
        if st.button("S2B T-Shirt 出面单", use_container_width=True):
            run_batch_process(order_ids, "T-Shirt", tokens.get("T-Shirt"), max_workers=max_workers)

    with col3:
        if st.button("S2B 3D 出面单", use_container_width=True):
            run_batch_process(order_ids, "3D", tokens.get("3D"), max_workers=max_workers)


def process_single_order(order_id, token, label):
    """
    Worker function executed in parallel. 
    Returns a tuple of (order_id, success_status, error_message)
    """
    result = push_delivery_print(order_id, token)
    return {
        "订单号": order_id,
        "渠道": label,
        "状态": "成功" if result.get("ok") else "失败",
        "HTTP状态": result.get("http_status") or "",
        "接口信息": result.get("message") or "",
    }


def normalize_order_ids(order_ids):
    if order_ids is None:
        return []
    if isinstance(order_ids, str):
        candidates = order_ids.replace(",", "\n").splitlines()
    else:
        candidates = order_ids

    clean_ids = []
    seen = set()
    for order_id in candidates:
        clean_order_id = str(order_id or "").strip()
        if not clean_order_id or clean_order_id in seen:
            continue
        clean_ids.append(clean_order_id)
        seen.add(clean_order_id)
    return clean_ids


def run_batch_process(order_ids, label, token, max_workers=5):
    ids_to_scan = normalize_order_ids(order_ids)
    if not ids_to_scan:
        st.warning(f"{label} 没有可出面单的订单号。")
        return []
    if not token:
        st.error(f"{label} token 为空，请检查 Streamlit secrets 的 s2b_tokens 配置。")
        return

    total_orders = len(ids_to_scan)
    worker_count = max(1, min(max_workers, total_orders))

    progress_bar = st.progress(0)
    status_text = st.empty()
    rows = []

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(process_single_order, order_id, token, label): order_id
            for order_id in ids_to_scan
        }

        for i, future in enumerate(as_completed(futures)):
            row = future.result()
            rows.append(row)

            completion_percentage = (i + 1) / total_orders
            progress_bar.progress(completion_percentage)
            status_text.text(
                f"{label} 出面单中：已处理 {i + 1}/{total_orders} | 当前订单：{row['订单号']}"
            )

    result_df = pd.DataFrame(rows).sort_values(by=["状态", "订单号"]).reset_index(drop=True)
    st.session_state.s2b_scan_result_df = result_df
    success_count = len(result_df[result_df["状态"] == "成功"])
    failed_count = total_orders - success_count
    status_text.success(f"{label} 出面单完成：成功 {success_count}，失败 {failed_count}。")

    return rows
