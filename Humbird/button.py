import streamlit as st
from Humbird.api import fetch_humbird_page, fetch_humbird_order_details

def render_humbird_workflow():
    st.title("🕊️ Humbird Order Workflow")

    # if st.button("Step 1: Fetch Page IDs"):
    #     # Step 1: Get the list of order_ids (Ensure your first function pulls r.get('order_id'))
    #     ids = fetch_humbird_page()
    #     if ids:
    #         st.session_state.humbird_order_ids = ids
    #         st.success(f"Found {len(ids)} Order IDs.")
    #         st.write(ids)
    #     else:
    #         st.error("Failed to fetch IDs. Sign/Token expired?")

    # if "humbird_order_ids" in st.session_state:
    if st.button("Step 1: Fetch Full Details for these IDs"):
        with st.spinner("Fetching details..."):
            # Step 2: Pass those IDs into the second function
            response_data = fetch_humbird_order_details()
           
            tracking_numbers = []
            # print("Full Detail Response:", response_data)  # Debug print to inspect the structure
            if response_data.get("result_code") == 200:
                orders = response_data.get("data", [])
                for order in orders:
    # Get th    e third_detail dictionary
                    third_detail = order.get("third_detail", {})
    # Get th    e list of tracking numbers (usually contains just one)
                    numbers = third_detail.get("track_number_list", [])
    
    # Add them to our main list
                tracking_numbers.extend(numbers)
        if response_data.get("result_code") == 200 and tracking_numbers:
            st.success("Details Received!")
            st.json(tracking_numbers ) # This contains your 'third_detail' info
        else:
            st.error("Detail fetch failed. Sign for the Detail API might be different/expired.")