import pandas as pd
import streamlit as st

from usps_website_batches import build_usps_website_batches, filter_usps_tracking_rows


def build_usps_batch_data(df):
    usps_df = filter_usps_tracking_rows(df)
    batches, mapping_rows = build_usps_website_batches(usps_df)
    return pd.DataFrame(batches), pd.DataFrame(mapping_rows)


def render_usps_batch_tables(df, key_prefix, expanded=True, table_height=720):
    batches_df, mapping_df = build_usps_batch_data(df)

    with st.expander("📮 USPS 35个一组批量查询链接", expanded=expanded):
        if batches_df.empty:
            st.info("没有找到可用于批量查询的 USPS 追踪号。")
        else:
            st.dataframe(
                batches_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Batch": st.column_config.NumberColumn("批次"),
                    "Count": st.column_config.NumberColumn("数量"),
                    "USPS Batch Link": st.column_config.LinkColumn("USPS批量查询链接", display_text="打开批次")
                }
            )

    if not mapping_df.empty:
        with st.expander("🧾 USPS订单与追踪号对应表", expanded=expanded):
            st.data_editor(
                mapping_df.sort_values(by=["Tracking Number"]),
                use_container_width=True,
                hide_index=True,
                height=table_height,
                key=f"{key_prefix}_usps_mapping",
                column_config={
                    "Batch": st.column_config.NumberColumn("批次"),
                    "Position in Batch": st.column_config.NumberColumn("批次内序号"),
                    "Order ID": st.column_config.TextColumn("订单号"),
                    "Tracking Number": st.column_config.TextColumn("追踪号"),
                    "Website Status": st.column_config.TextColumn("官网状态"),
                    "Notes": st.column_config.TextColumn("备注")
                },
                disabled=["Batch", "Position in Batch", "Order ID", "Tracking Number"]
            )

    return batches_df, mapping_df
