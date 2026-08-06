import pandas as pd
import streamlit as st

from s2b.scanButton import render_S2B_scan_buttons


def parse_order_ids(raw_text):
    order_ids = []
    seen = set()
    for value in raw_text.replace(",", "\n").splitlines():
        order_id = value.strip()
        if not order_id or order_id in seen:
            continue
        order_ids.append(order_id)
        seen.add(order_id)
    return order_ids


st.set_page_config(layout="wide", page_title="S2B出面单")
st.title("S2B出面单")

st.caption("把 S2B 订单号粘贴进来，选择对应渠道后批量出面单。")

default_text = ""
if "df_input" in st.session_state and isinstance(st.session_state.df_input, pd.DataFrame):
    if "Order ID" in st.session_state.df_input.columns:
        default_ids = [
            str(order_id).strip()
            for order_id in st.session_state.df_input["Order ID"].tolist()
            if str(order_id).strip()
        ]
        default_text = "\n".join(default_ids)

raw_order_ids = st.text_area(
    "订单号",
    value=default_text,
    height=260,
    placeholder="每行一个订单号，也可以用逗号分隔。",
)

order_ids = parse_order_ids(raw_order_ids)

metric_col1, metric_col2 = st.columns(2)
metric_col1.metric("订单号数量", len(order_ids))
metric_col2.metric("去重后数量", len(order_ids))

max_workers = st.slider(
    "并发数",
    min_value=1,
    max_value=30,
    value=5,
    step=1,
    help="如果接口失败较多，先把并发数降到 3-5。",
)

render_S2B_scan_buttons(order_ids=order_ids, max_workers=max_workers)

if "s2b_scan_result_df" in st.session_state:
    result_df = st.session_state.s2b_scan_result_df
    st.dataframe(
        result_df,
        use_container_width=True,
        hide_index=True,
        height=520,
    )
    st.download_button(
        "下载结果 CSV",
        data=result_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="S2B出面单结果.csv",
        mime="text/csv",
        use_container_width=True,
    )
