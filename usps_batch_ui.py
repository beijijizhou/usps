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
            st.info("No USPS tracking numbers found for batching.")
        else:
            st.dataframe(
                batches_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "USPS Batch Link": st.column_config.LinkColumn("USPS Batch Link", display_text="Open Batch")
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
                    "Batch": st.column_config.NumberColumn("Batch"),
                    "Position in Batch": st.column_config.NumberColumn("Position"),
                    "Order ID": st.column_config.TextColumn("Order ID"),
                    "Tracking Number": st.column_config.TextColumn("Tracking Number"),
                    "Website Status": st.column_config.TextColumn("Website Status"),
                    "Notes": st.column_config.TextColumn("Notes")
                },
                disabled=["Batch", "Position in Batch", "Order ID", "Tracking Number"]
            )

    return batches_df, mapping_df
