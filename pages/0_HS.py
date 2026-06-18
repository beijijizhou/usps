import re
import streamlit as st
import requests

def login_to_factory():
    """
    Authenticates with the factory API and returns the access token.
    """
    url = "https://tshirt.riin.com/auth/api/auth/login"
    
    # Define the payload exactly as required by the API
    payload = {
        "username": "damo1",
        "password": "c7018409ffc927d2a7193c7b09bcd059",
        "clientId": "WEB"
    }
    
    # Standard headers for a JSON POST request
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        # Make the POST request with the JSON payload
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # Check if the HTTP request was successful (status code 200)
        if response.status_code == 200:
            data = response.json()
            
            # --- Token Extraction Logic ---
            # API architectures vary. We look for common token keys:
            token = (
                data.get("token") or 
                data.get("access_token") or 
                data.get("data", {}).get("token") or 
                data.get("data", {}).get("accessToken")
            )
            
            if token:
                print("Successfully logged in and retrieved token.")
                return token
            else:
                print(f"Login succeeded but token key not found in response: {data}")
                return None
        else:
            print(f"Login failed with status code {response.status_code}: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during authentication: {e}")
        return None
auth_token = login_to_factory()

def get_label_data(label_no):
 
    """The background function that talks to the tshirt.riin.com API."""
    url = "https://tshirt.riin.com/manufacture/deliverGoodsLabel/scan/labelNo"

    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": auth_token,
        "referer": "https://tshirt.riin.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
        "x-time-zone": "UTC-5"
    }

    cookies = {
        "authorized-token-FACTORY": auth_token,
        "_ga": "GA1.1.681259542.1764427466"
    }

    params = {"labelNo": label_no}

    try:
        response = requests.get(url, headers=headers,
                                cookies=cookies, params=params, timeout=10)
        return response
    except Exception as e:
        return str(e)


def render_HS_scanner_ui():
    """This is the function you call in your main app to display the scanner."""
    st.subheader("📦 汉森自动扫面单")

    print(f"Factory Auth Token: {auth_token}")
    # Changed to text_area to support the long list of labels
    label_input = st.text_area(
        "Label Numbers", placeholder="Paste labels separated by commas or new lines...", key="scan_lbl_input", height=200)

    if st.button("Execute Scan", width='stretch'):
        if not label_input:
            st.warning("Please enter labels.")
            return

        # Split by commas, newlines, or spaces and remove empty items
        labels = [l.strip() for l in re.split(
            r'[,\n\s]+', label_input) if l.strip()]

        if not labels:
            st.warning("No valid labels found.")
            return

        progress_text = st.empty()
        progress_bar = st.progress(0)

        # Loop through each label in the list
        for i, label in enumerate(labels):
            progress_text.text(f"Scanning {i+1}/{len(labels)}: {label}")
            progress_bar.progress((i + 1) / len(labels))

            res = get_label_data(label)

            # Use an expander for each result to keep the UI clean
            with st.expander(f"Result for {label}"):
                if isinstance(res, str):
                    st.error(f"Connection Error: {res}")
                elif res.status_code == 200:
                    data = res.json()
                    if data.get("code") == 200:
                        st.success("Label Details Found")
                    else:
                        st.error(
                            f"API Message: {data.get('msg', 'Unknown Error')}")
                    st.json(data)
                elif res.status_code == 401:
                    st.error("Unauthorized: Token has likely expired.")
                    break  # Stop if token is dead
                else:
                    st.error(f"Error {res.status_code}: {res.text}")

        progress_text.text("✅ Scan Complete")
render_HS_scanner_ui()