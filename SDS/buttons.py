import streamlit as st
# Ensure this points to your fetch script
from SDS.factoryFetch import factory_fetch_records


def render_SDS_3_fetch_button():
    """
    Renders the button to pull latest records from the SDS 3 Factory API.
    """
    st.subheader("📦 工厂订单")

    # Initialize session state for records if it doesn't exist
    if "order_list" not in st.session_state:
        st.session_state.order_list = []

    if st.button("获取工厂订单", width='stretch'):
        with st.spinner("正在访问工厂接口..."):
            # Call your function
            records = factory_fetch_records()

            if records:
                # Store in session state so other buttons can see it
                st.session_state.order_list = records
                st.success(
                    f"已成功获取 {len(records)} 个订单号。")
            else:
                st.error("没有找到订单，或接口请求失败。请检查 Cookie/Token。")

    # Show a small preview of what was fetched
    if st.session_state.order_list:
        with st.expander("查看已获取订单号"):
            st.write(st.session_state.order_list)

    return st.session_state.order_list
