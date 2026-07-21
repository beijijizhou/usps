# DEBUG INFO
from SDS.buttons import render_SDS_3_fetch_button
from Humbird.button import render_humbird_workflow
from rbt.rbt_button_ui import render_rbt_button_ui
from usps_utils import run_usps_tracking_process
import pandas as pd
import streamlit as st
from s2b.scanButton import render_S2B_scan_buttons
import os
import sys
from usps_batch_ui import render_usps_batch_tables

from utility import get_data_metrics
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Add that directory to the very beginning of the Python path
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
st.set_page_config(layout="wide", page_title="物流单号批量查询")

st.title("📦 物流单号批量查询")

# 1. Create an empty starting sheet (2 columns)
if 'df_input' not in st.session_state:
    st.session_state.df_input = pd.DataFrame(
        [{"Order ID": "", "Tracking Number": ""}],
    )

st.subheader("第一步：把订单号和物流单号复制到表格里")
st.caption(
    "可以直接从 Excel 或 Google Sheets 复制粘贴到下方表格。")

# The Data Editor acts as your "Spreadsheet" input


edited_df = st.data_editor(
    st.session_state.df_input,
    num_rows="dynamic",  # Allows users to add/delete rows
    width='stretch',
    column_config={
        "Order ID": st.column_config.TextColumn("订单号"),
        "Tracking Number": st.column_config.TextColumn("物流单号（必填）"),
    }
)
if edited_df is not None:
    st.session_state.df_input = edited_df

c1, c2, _ = st.columns([2, 2, 4])
with c1:
    sort_by = st.selectbox("排序方式：", ["不排序", "订单号", "物流单号"])
with c2:
    if st.button("🔄 应用排序", use_container_width=True):
        if sort_by == "订单号":
            st.session_state.df_input = st.session_state.df_input.sort_values(
                by="Order ID", key=lambda col: col.fillna("").astype(str)
            ).reset_index(drop=True)
            st.rerun()
        elif sort_by == "物流单号":
            st.session_state.df_input = st.session_state.df_input.sort_values(
                by="Tracking Number", key=lambda col: col.fillna("").astype(str)
            ).reset_index(drop=True)
            st.rerun()

c1, c2 = st.columns(2)
count_orders, count_tracking = get_data_metrics(st.session_state.df_input)

c1.metric("📦 订单号数量", count_orders)
c2.metric("🚚 物流单号数量", count_tracking)
# 2. Process Button
lookup_col, api_col = st.columns(2)
with lookup_col:
    build_batches = st.button(
        "生成 USPS 35个一组查询链接", type="primary", use_container_width=True)
with api_col:
    start_api_tracking = st.button(
        "使用 USPS 付费API查询状态", use_container_width=True)

if build_batches:
    df_clean = edited_df.fillna("").astype(str)
    valid_data = df_clean[df_clean["Tracking Number"].str.strip() != ""]
    if valid_data.empty:
        st.warning("请至少输入一个物流单号。")
    else:
        st.session_state.usps_website_source_df = valid_data

if start_api_tracking:
    # Filter out any rows where the tracking number is empty
    df_clean = edited_df.fillna("").astype(str)
    valid_data = df_clean[df_clean["Tracking Number"].str.strip() != ""]
    if valid_data.empty:
        st.warning("请至少输入一个物流单号。")
    else:
        try:
            status_message = st.empty()
            progress_bar = st.progress(0, text="正在初始化...")
            results = run_usps_tracking_process(valid_data, progress_bar=progress_bar,
                                                status_text=status_message)
            if results:
                final_df = pd.DataFrame(results)
                st.dataframe(
                    final_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Order ID": st.column_config.TextColumn("订单号"),
                        "Tracking Number": st.column_config.TextColumn("物流单号"),
                        "Status": st.column_config.TextColumn("状态"),
                        "Last Updated": st.column_config.TextColumn("最后更新时间"),
                        "Location": st.column_config.TextColumn("地点"),
                        "API Message": st.column_config.TextColumn("API信息"),
                        "USPS Link": st.column_config.LinkColumn("USPS链接", display_text="打开USPS")
                    }
                )
            else:
                st.info("没有找到有效的 USPS 物流单号。")

        except Exception as e:
            st.error(f"发生错误：{str(e)}")

if "usps_website_source_df" in st.session_state:
    st.subheader("第二步：USPS官网批量查询链接")
    render_usps_batch_tables(
        st.session_state.usps_website_source_df,
        key_prefix="main_pasted_table",
        expanded=True
    )


# render_S2B_scan_buttons(order_ids=edited_df["Order ID"].tolist())

# render_SDS_3_fetch_button()

# render_sds3_widgets()
# render_humbird_workflow()


# render_rbt_button_ui()
