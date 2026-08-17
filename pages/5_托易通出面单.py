from datetime import date, timedelta

import pandas as pd
import streamlit as st

from toyitool.api import fetch_order_pages, outbound_orders


def get_saved_authorization():
    try:
        toyitool_config = st.secrets.get("toyitool", {})
    except Exception:
        toyitool_config = {}
    return (
        toyitool_config.get("authorization")
        or toyitool_config.get("token")
        or ""
    )


st.set_page_config(layout="wide", page_title="托易通出面单")
st.title("托易通出面单")

st.caption("第一步：从托易通订单列表接口获取昨天到今天的生产中订单。当前页面不会执行出面单。")

saved_authorization = get_saved_authorization()
authorization = st.text_input(
    "Authorization / Token",
    value=saved_authorization,
    type="password",
    help="可以粘贴完整的 Bearer token，也可以只粘贴 token 本体。部署时建议放到 secrets 的 [toyitool] token。",
)

control_col1, control_col2, control_col3 = st.columns(3)
with control_col1:
    time_type = st.selectbox(
        "时间类型",
        options=["s.assign_time"],
        index=0,
    )
with control_col2:
    start_date = st.date_input("开始日期", value=date.today() - timedelta(days=1))
with control_col3:
    end_date = st.date_input("结束日期", value=date.today())

st.info("当前固定只获取生产中订单。")

page_col1, page_col2 = st.columns(2)
with page_col1:
    page_size = st.number_input("每页数量", min_value=10, max_value=500, value=200, step=10)
with page_col2:
    max_pages = st.number_input("最多拉取页数", min_value=1, max_value=500, value=5, step=1)

if st.button("获取订单号和订单ID", type="primary", use_container_width=True):
    if not authorization.strip():
        st.error("请先输入托易通 Authorization / Token。")
    elif start_date and end_date and start_date > end_date:
        st.error("开始日期不能晚于结束日期。")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(page_num, pages_to_fetch, fetched, total):
            progress_bar.progress(page_num / pages_to_fetch if pages_to_fetch else 0)
            status_text.text(
                f"正在拉取：第 {page_num}/{pages_to_fetch} 页 | 已获取 {fetched} 条 | 接口总数 {total}"
            )

        with st.spinner("正在从托易通获取订单列表..."):
            try:
                result = fetch_order_pages(
                    authorization=authorization,
                    page_size=int(page_size),
                    max_pages=int(max_pages),
                    time_type=time_type,
                    start_date=start_date,
                    end_date=end_date,
                    order_status="PRODUCTION",
                    on_progress=update_progress,
                )
                st.session_state.toyitool_order_rows = result["rows"]
                st.session_state.toyitool_order_summary = {
                    "total": result["total"],
                    "fetched": result["fetched"],
                    "production": result["fetched"],
                    "order_status": "PRODUCTION",
                    "pages_fetched": result["pages_fetched"],
                }
                status_text.success(
                    f"获取完成：生产中订单 {result['fetched']} 条。"
                )
            except Exception as exc:
                progress_bar.empty()
                status_text.empty()
                st.error(f"获取失败：{exc}")

if "toyitool_order_rows" in st.session_state:
    rows = st.session_state.toyitool_order_rows
    summary = st.session_state.get("toyitool_order_summary", {})
    result_df = pd.DataFrame(rows)

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("生产中总数", summary.get("total", len(result_df)))
    metric_col2.metric("已拉取生产中", summary.get("fetched", len(result_df)))
    metric_col3.metric("页数", summary.get("pages_fetched", 1))

    st.dataframe(
        result_df,
        use_container_width=True,
        hide_index=True,
        height=620,
    )

    st.download_button(
        "下载订单列表 CSV",
        data=result_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="托易通订单号列表.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.divider()
    st.subheader("第二步：托易通出面单 / 出库")
    st.warning("这个操作会调用托易通 outbound 接口，可能改变订单状态。请先确认当前列表只包含需要处理的生产中订单。")

    outbound_order_ids = []
    if not result_df.empty and "订单ID" in result_df.columns:
        outbound_order_ids = [
            str(order_id).strip()
            for order_id in result_df["订单ID"].tolist()
            if str(order_id).strip()
        ]

    outbound_col1, outbound_col2 = st.columns([2, 1])
    with outbound_col1:
        confirm_outbound = st.checkbox(
            f"确认对当前 {len(outbound_order_ids)} 个生产中订单执行托易通出面单 / 出库",
            value=False,
        )
    with outbound_col2:
        run_outbound = st.button(
            "执行托易通出面单",
            type="primary",
            use_container_width=True,
            disabled=not confirm_outbound or not outbound_order_ids,
        )

    if run_outbound:
        with st.spinner("正在提交托易通 outbound 接口..."):
            try:
                outbound_result = outbound_orders(authorization, outbound_order_ids)
                st.session_state.toyitool_outbound_result = outbound_result
                if outbound_result["ok"]:
                    st.success(
                        f"提交成功：共 {outbound_result['order_count']} 个订单。接口信息：{outbound_result['message']}"
                    )
                else:
                    st.error(
                        f"提交失败：HTTP {outbound_result['http_status']}，接口信息：{outbound_result['message']}"
                    )
            except Exception as exc:
                st.error(f"提交失败：{exc}")

if "toyitool_outbound_result" in st.session_state:
    outbound_result = st.session_state.toyitool_outbound_result
    st.json({
        "成功": outbound_result.get("ok"),
        "HTTP状态": outbound_result.get("http_status"),
        "订单数量": outbound_result.get("order_count"),
        "接口信息": outbound_result.get("message"),
    })
