import streamlit as st

def render_platform_dropdown():
    """
    Renders a platform selection dropdown.
    Returns the selected platform string.
    """
    st.markdown("### 🌐 选择工作平台")
    
    # Define the available platforms based on your requirement
    platforms = [
        "1号线",
        "2号线",
        "忆点万象",
        "3D热转印"
    ]

    if "selected_platform" not in st.session_state:
        st.session_state.selected_platform = "3D热转印"
    
    # Store choice in session state if you need persistence across tabs, 
    # otherwise a local return is perfectly clean.
    selected_platform = st.selectbox(
        "切换生产线 / 平台 :",
        options=platforms,
        key="selected_platform"
    )
    
    return selected_platform
