import pandas as pd
import streamlit as st

from s2b.batches import S2BBatchError, get_batch_order_codes, list_batches
from s2b.scan import get_s2b_tokens
from s2b.scanButton import S2B_CHANNELS, render_S2B_scan_buttons, run_batch_process


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

st.divider()
st.subheader("按批次出面单")
st.caption("读取最近的 S2B 生产批次，可以出全部批次的面单，也可以只出勾选批次的面单。")

batch_col1, batch_col2 = st.columns([3, 1])
batch_channel = batch_col1.radio(
    "批次渠道",
    [label for label, _ in S2B_CHANNELS],
    horizontal=True,
)
batch_limit = batch_col2.number_input("读取批次数", min_value=1, max_value=200, value=50, step=10)
batch_token = get_s2b_tokens().get(batch_channel)
batches_state = st.session_state.setdefault("s2b_batches", {})

if st.button("读取批次", use_container_width=True):
    try:
        with st.spinner(f"正在读取 {batch_channel} 最近 {batch_limit} 个批次…"):
            batches_state[batch_channel] = list_batches(batch_token, limit=batch_limit)
    except S2BBatchError as error:
        st.error(f"读取 {batch_channel} 批次失败：{error}")

batches = batches_state.get(batch_channel)
if batches is not None:
    if not batches:
        st.info(f"{batch_channel} 没有读到批次。")
    else:
        batch_df = pd.DataFrame(batches)
        batch_df.insert(0, "选择", False)
        edited_df = st.data_editor(
            batch_df,
            use_container_width=True,
            hide_index=True,
            height=360,
            disabled=[column for column in batch_df.columns if column != "选择"],
            key=f"s2b_batch_editor_{batch_channel}",
        )
        selected_batches = edited_df.loc[edited_df["选择"], "批次号"].tolist()
        all_batches = edited_df["批次号"].tolist()

        action_col1, action_col2 = st.columns(2)
        target_batches = None
        if action_col1.button(
            f"勾选批次出面单（{len(selected_batches)} 个）",
            use_container_width=True,
            type="primary",
            disabled=not selected_batches,
        ):
            target_batches = selected_batches
        if action_col2.button(f"全部批次出面单（{len(all_batches)} 个）", use_container_width=True):
            target_batches = all_batches

        if target_batches:
            order_batches = {}
            read_progress = st.progress(0)
            read_status = st.empty()
            failed_batches = []
            for i, batch_number in enumerate(target_batches):
                read_status.text(f"读取批次订单：{i + 1}/{len(target_batches)} | {batch_number}")
                try:
                    for order_code in get_batch_order_codes(batch_token, batch_number):
                        order_batches.setdefault(order_code, []).append(batch_number)
                except S2BBatchError as error:
                    failed_batches.append(batch_number)
                    st.warning(f"批次 {batch_number} 读取失败：{error}")
                read_progress.progress((i + 1) / len(target_batches))
            read_status.text(
                f"已读取 {len(target_batches) - len(failed_batches)} 个批次，共 {len(order_batches)} 个订单号。"
            )

            if order_batches:
                run_batch_process(list(order_batches), batch_channel, batch_token, max_workers=max_workers)
                result_df = st.session_state.get("s2b_scan_result_df")
                if isinstance(result_df, pd.DataFrame) and "订单号" in result_df.columns:
                    result_df.insert(
                        0,
                        "批次号",
                        result_df["订单号"].map(lambda code: "、".join(order_batches.get(code, []))),
                    )
            else:
                st.warning("选中的批次里没有读到订单号。")

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
