import streamlit as st
from SDS.factoryFetch import factory_fetch_records # Ensure this points to your fetch script

def render_SDS_3_fetch_button():
    """
    Renders the button to pull latest records from the SDS 3 Factory API.
    """
    st.subheader("📦 SDS 3 Factory Orders")
    
    # Initialize session state for records if it doesn't exist
    if "order_list" not in st.session_state:
        st.session_state.order_list = []

    if st.button("Fetch SDS 3 Records", use_container_width=True):
        with st.spinner("Accessing Factory API..."):
            # Call your function
            records = factory_fetch_records()
            
            if records:
                # Store in session state so other buttons can see it
                st.session_state.order_list = records
                st.success(f"Successfully fetched {len(records)} order numbers.")
            else:
                st.error("No records found or API error. Check your Cookie/Token.")

    # Show a small preview of what was fetched
    if st.session_state.order_list:
        with st.expander("View Fetched IDs"):
            st.write(st.session_state.order_list)
            
    return st.session_state.order_list