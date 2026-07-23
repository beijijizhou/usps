from datetime import date

import pandas as pd
import streamlit as st

from SDS.usps_label_range_export import (
    DEFAULT_SOURCE_PATH,
    export_usps_range,
    uploaded_file_to_buffer,
)


PLATFORMS = ["全部平台", "1号线", "2号线", "忆点万象", "3D热转印"]
PREVIEW_COLUMNS = ["平台", "SDS订单号", "销售订单号", "物流单号", "物流渠道", "开始时间", "面单PDF"]


def get_source_file(uploaded_file):
    if uploaded_file is not None:
        return uploaded_file_to_buffer(uploaded_file), uploaded_file.name
    if DEFAULT_SOURCE_PATH.exists():
        return DEFAULT_SOURCE_PATH, DEFAULT_SOURCE_PATH.name
    return None, ""


st.set_page_config(layout="wide", page_title="USPS面单导出")
st.title("USPS面单导出")

st.caption("从历史面单 Excel 中按日期范围筛选 USPS 物流，并导出新的 Excel。")

uploaded_file = st.file_uploader(
    "历史面单 Excel",
    type=["xlsx"],
    help="如果服务器本地已有历史面单 Excel，可以不上传；否则请上传包含“面单数据”表的历史 Excel。",
)

source_file, source_name = get_source_file(uploaded_file)
if source_file is None:
    st.warning("未找到本地历史面单 Excel。请先上传一个历史面单 Excel。")
else:
    st.info(f"当前数据源：{source_name}")

control_col1, control_col2, control_col3 = st.columns([1, 1, 1])
with control_col1:
    selected_platform = st.selectbox("平台", PLATFORMS, index=2)
with control_col2:
    start_date = st.date_input("开始日期", value=date(2026, 5, 20))
with control_col3:
    end_date = st.date_input("结束日期", value=date(2026, 7, 20))

run_export = st.button(
    "生成 USPS 面单 Excel",
    type="primary",
    use_container_width=True,
    disabled=source_file is None,
)

if run_export:
    if start_date > end_date:
        st.error("开始日期不能晚于结束日期。")
    else:
        with st.spinner("正在筛选 USPS 面单数据..."):
            try:
                result = export_usps_range(
                    source=source_file,
                    start_date=start_date,
                    end_date=end_date,
                    platform=selected_platform,
                )
                st.session_state.usps_label_export_result = result
            except Exception as exc:
                st.error(f"导出失败：{exc}")

if "usps_label_export_result" in st.session_state:
    result = st.session_state.usps_label_export_result
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("历史数据行数", result["source_rows"])
    metric_col2.metric("USPS结果行数", result["filtered_rows"])
    metric_col3.metric("文件大小", f"{len(result['workbook_bytes']) / 1024 / 1024:.1f} MB")

    if result["filtered_rows"] == 0:
        st.warning("这个范围内没有筛选到 USPS 面单。")
    else:
        preview_df = pd.DataFrame(result["records"])
        visible_columns = [column for column in PREVIEW_COLUMNS if column in preview_df.columns]
        st.dataframe(
            preview_df[visible_columns],
            use_container_width=True,
            hide_index=True,
            height=520,
            column_config={
                "面单PDF": st.column_config.LinkColumn("面单PDF", display_text="打开面单")
            },
        )

    st.download_button(
        "下载 Excel",
        data=result["workbook_bytes"],
        file_name=result["output_name"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
