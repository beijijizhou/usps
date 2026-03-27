import streamlit as st
from Humbird.api import fetch_humbird_page, fetch_humbird_order_details

def render_humbird_workflow():
    st.title("🕊️ Humbird Order Workflow")

    if st.button("Step 1: Fetch Page IDs"):
        # Step 1: Get the list of order_ids (Ensure your first function pulls r.get('order_id'))
        ids = fetch_humbird_page()
        if ids:
            st.session_state.humbird_order_ids = ids
            st.success(f"Found {len(ids)} Order IDs.")
            st.write(ids)
        else:
            st.error("Failed to fetch IDs. Sign/Token expired?")

    if "humbird_order_ids" in st.session_state:
        if st.button("Step 2: Fetch Full Details for these IDs"):
            with st.spinner("Fetching details..."):
                # Step 2: Pass those IDs into the second function
                details = fetch_humbird_order_details(st.session_state.humbird_order_ids)
                
                if details:
                    st.success("Details Received!")
                    st.json(details) # This contains your 'third_detail' info
                else:
                    st.error("Detail fetch failed. Sign for the Detail API might be different/expired.")