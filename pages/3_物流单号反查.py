from datetime import date

import pandas as pd
import streamlit as st

from SDS.pre_scan import DEFAULT_MAX_WORKERS
from SDS.producedTrackingFetch import find_tracking_numbers_in_platform_history, parse_tracking_numbers


PLATFORMS = ["1号线", "2号线", "忆点万象", "3D热转印"]
ALL_PLATFORM_OPTION = "全部平台"
TABLE_HEIGHT = 720
COLUMN_LABELS = {
    "Platform": "平台",
    "Order ID": "订单号",
    "Merchant Order No": "销售订单号",
    "Tracking Number": "物流单号",
    "Carrier": "渠道",
    "Factory Status": "工厂状态",
    "Begin Time": "开始时间",
    "Finished Time": "完成时间",
    "Ship Time": "发货时间",
    "PDF": "面单PDF",
    "Status": "状态",
    "Match Status": "匹配状态",
}


def set_platform_temporarily(platform_name):
    previous_platform = st.session_state.get("selected_platform")
    st.session_state.selected_platform = platform_name
    return previous_platform


def restore_platform(previous_platform):
    if previous_platform:
        st.session_state.selected_platform = previous_platform
    elif "selected_platform" in st.session_state:
        del st.session_state.selected_platform


def localize_dataframe(df):
    return df.rename(columns={key: value for key, value in COLUMN_LABELS.items() if key in df.columns})


def run_reverse_lookup(raw_tracking_numbers, selected_platform, start_date, end_date, max_workers):
    target_tracking_numbers = parse_tracking_numbers(raw_tracking_numbers)
    if not target_tracking_numbers:
        st.warning("请先粘贴需要反查的 tracking number。")
        return

    platforms_to_search = PLATFORMS if selected_platform == ALL_PLATFORM_OPTION else [
        selected_platform]
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_found_rows = []
    found_tracking_numbers = set()
    previous_platform = st.session_state.get("selected_platform")

    try:
        for platform_index, platform_name in enumerate(platforms_to_search, start=1):
            set_platform_temporarily(platform_name)

            def update_progress(queried, total, result, current_platform, found_count, target_count):
                platform_base = (platform_index - 1) / len(platforms_to_search)
                platform_fraction = (
                    queried / total if total else 0) / len(platforms_to_search)
                progress_bar.progress(
                    min(platform_base + platform_fraction, 1.0))
                status_text.text(
                    f"{current_platform} 多线程反查中：已查 {queried}/{total} | 已找到 {found_count}/{target_count} | 当前订单：{result.get('Order ID')}"
                )

            _, found_rows, _ = find_tracking_numbers_in_platform_history(
                raw_tracking_numbers=raw_tracking_numbers,
                start_date=start_date,
                end_date=end_date,
                platform_name=platform_name,
                max_workers=max_workers,
                on_progress=update_progress,
            )
            for row in found_rows:
                tracking_number = str(row.get("Tracking Number", "")).strip()
                if tracking_number not in found_tracking_numbers:
                    all_found_rows.append(row)
                    found_tracking_numbers.add(tracking_number)

            if found_tracking_numbers >= set(target_tracking_numbers):
                break
    finally:
        restore_platform(previous_platform)

    missing_rows = [
        {
            "Platform": "",
            "Order ID": "",
            "Merchant Order No": "",
            "Tracking Number": tracking_number,
            "Carrier": "",
            "Factory Status": "",
            "Begin Time": "",
            "Finished Time": "",
            "Ship Time": "",
            "PDF": "",
            "Status": "所选平台历史数据中未找到",
            "Match Status": "未找到",
        }
        for tracking_number in target_tracking_numbers
        if tracking_number not in found_tracking_numbers
    ]
    result_rows = all_found_rows + missing_rows
    result_df = pd.DataFrame(result_rows)
    st.session_state.reverse_lookup_result_df = result_df
    progress_bar.empty()
    status_text.success(
        f"反查完成：输入 {len(target_tracking_numbers)} 个，找到 {len(all_found_rows)} 个，未找到 {len(missing_rows)} 个。"
    )


st.set_page_config(layout="wide", page_title="物流单号反查")
st.title("🔎 物流单号反查")

selected_platform = st.selectbox(
    "选择平台",
    options=[ALL_PLATFORM_OPTION, *PLATFORMS],
    index=0,
    help="选择全部平台时，会依次查询所有 SDS 平台；找到后会停止继续查同一个 tracking number。"
)

date_col1, date_col2, worker_col = st.columns([1, 1, 1])
with date_col1:
    start_date = st.date_input("开始日期", value=date(date.today().year, 5, 1))
with date_col2:
    end_date = st.date_input("结束日期", value=date.today())
with worker_col:
    max_workers = st.slider(
        "并发线程数",
        min_value=10,
        max_value=1000,
        value=DEFAULT_MAX_WORKERS,
        step=10,
    )

raw_tracking_numbers = st.text_area(
    "Tracking number 列表",
    height=260,
    placeholder="把 tracking number 粘贴到这里，每行一个；可以包含 label_id 表头。",
)

if st.button("🚀 开始反查", type="primary", use_container_width=True):
    run_reverse_lookup(
        raw_tracking_numbers=raw_tracking_numbers,
        selected_platform=selected_platform,
        start_date=start_date,
        end_date=end_date,
        max_workers=max_workers,
    )

if "reverse_lookup_result_df" in st.session_state:
    result_df = st.session_state.reverse_lookup_result_df
    localized_df = localize_dataframe(result_df)
    found_count = len(result_df[result_df["Match Status"]
                      == "已找到"]) if "Match Status" in result_df else 0
    missing_count = len(result_df) - found_count

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("输入数量", len(result_df))
    metric_col2.metric("已找到", found_count)
    metric_col3.metric("未找到", missing_count)

    st.dataframe(
        localized_df,
        use_container_width=True,
        hide_index=True,
        height=TABLE_HEIGHT,
        column_config={
            "面单PDF": st.column_config.LinkColumn("面单PDF", display_text="打开面单")
        },
    )
    st.download_button(
        "⬇️ 下载反查结果 CSV",
        data=localized_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="tracking反查结果.csv",
        mime="text/csv",
        use_container_width=True,
    )
