import streamlit as st
from rbt.scanner_utils import get_label_data, get_dynamic_time_range
import re

def render_rbt_button_ui():
    st.divider()
    st.subheader("🚀 RBT - 平台相关扫描")
    
    # 1. Setup the Time Range (Internal use or display)
    times = get_dynamic_time_range(days_before=1, days_after=1)
    st.info(f"Scan Range: {times['startTime']} to {times['endTime']}")

    # 2. Input Area
    label_input = st.text_area(
        "Paste labels (Comma or Newline separated)", 
        placeholder="LB260405..., LB260405...",
        key="rbt_input_area"
    )

    # 3. The RBT Button
    if st.button("🔥 Run RBT Scan", type="primary", use_container_width=True):
        if not label_input:
            st.warning("Please enter labels first.")
            return

        # Clean the input using regex
        labels = [l.strip() for l in re.split(r'[,\n\s]+', label_input) if l.strip()]
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Execute loop
        for i, label in enumerate(labels):
            status_text.text(f"Scanning {i+1}/{len(labels)}: {label}")
            
            res = get_label_data(label)
            
            with st.expander(f"Result: {label}"):
                if isinstance(res, str):
                    st.error(f"Error: {res}")
                elif res.status_code == 200:
                    data = res.json()
                    if data.get("code") == 200:
                        st.success("Verified")
                    else:
                        st.error(data.get("msg", "Unknown API error"))
                    st.json(data)
                elif res.status_code == 401:
                    st.error("Hard-coded Token Expired!")
                    break
            
            progress_bar.progress((i + 1) / len(labels))

        status_text.success(f"Successfully processed {len(labels)} labels.")