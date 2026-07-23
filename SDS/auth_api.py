import streamlit as st
import requests
import time
from SDS.credentials import get_platform_credentials, get_selected_platform

def login_to_SDS_factory():
    """
    Authenticates with the Factory Production API environment.
    """
    current_platform = get_selected_platform()
    creds, error_message = get_platform_credentials("factory_credentials", current_platform)
    if error_message:
        st.error(f"❌ 工厂账号配置错误：{error_message}")
        return None

    url = "https://factory-api.sdspod.com/login"
    
    payload = {
        "contact_tel": creds.get("contact_tel", "19959560739"),
        "extraInfo": creds.get("extraInfo", "eyJmaW5nZXJwcmludElkIjoiMzBlOTYzOGIxNzZmN2U1NjI3OTQwOWE0M2YyN2NjNTMiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoTWFjaW50b3NoOyBJbnRlbCBNYWMgT1MgWCAxMF8xNV83KSBBcHBsZVdlYktpdC81MzcuMzYgKEtIVE1MLCBsaWtlIEdlY2tvKSBDaHJvbWUvMTQ5LjAuMC4wIFNhZmFyaS81MzcuMzYiLCJocmVmIjoiaHR0cHM6Ly9mYWN0b3J5LnNkc2RpeS5jb20vIy91c2VyL2xvZ2luIn0="),
        "factory_code": creds.get("factory_code", "NY004"),
        "password": creds.get("password", "19959560739")
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    try:
        
        response = requests.post(url, json=payload, headers=headers, timeout=100)
        if response.status_code == 200:
            data = response.json()
            token = data.get("data", {}).get("access_token") or data.get("data", {}).get("token")            
            if token:
                return token
            else:
                st.error(f"⚠️ Factory Login succeeded, but token key not found: {data}")
                return None
        else:
            st.error(f"❌ Factory Login HTTP Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"🚨 Factory Connection Failure: {e}")
        return None


def login_to_qa():
    """
    Authenticates with the QA API environment using g-pod-api.
    """
    current_platform = get_selected_platform()
    creds, error_message = get_platform_credentials("qa_credentials", current_platform)
    if error_message:
        st.error(f"❌ QA账号配置错误：{error_message}")
        return None

    # Base URL for the QA Auth Endpoint
    url = "https://g-pod-api.sdspod.com/pod/auth/login"
    
    # Generate dynamic timestamp milliseconds parameter (e.g., ?t=1782085557003)
    timestamp_ms = int(time.time() * 1000)
    params = {"t": timestamp_ms}
    
    # Updated payload schema strictly matching your QA payload layout
    payload = {
        "extraInfo": creds.get("extraInfo", "eyJmaW5nZXJwcmludElkIjoiMzBlOTYzOGIxNzZmN2U1NjI3OTQwOWE0M2YyN2NjNTMiLCJ1c2VyQWdlbnQiOiJNb3ppbGxhLzUuMCAoTWFjaW50b3NoOyBJbnRlbCBNYWMgT1MgWCAxMF8xNV83KSBBcHBsZVdlYktpdC81MzcuMzYgKEtIVE1MLCBsaWtlIEdlY2tvKSBDaHJvbWUvMTQ5LjAuMC4wIFNhZmFyaS81MzcuMzYiLCJocmVmIjoiaHR0cHM6Ly9nbWFuYWdlLnNkc3BvZC5jb20vdXNlci9sb2dpbiJ9"),
        "no": creds.get("no", "sdspod"),
        "password": creds.get("password", "19959560739"),
        "username": creds.get("username", "19959560739")
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    try:
        # Appends the ?t= timestamp directly into the URL stream parameters automatically
        response = requests.post(url, json=payload, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token") or data.get("data", {}).get("token") or data.get("data", {}).get("accessToken")
            if token:
                return token
            else:
                st.error(f"⚠️ QA Login succeeded, but token key not found in response structure: {data}")
                return None
        else:
            st.error(f"❌ QA Login HTTP Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        st.error(f"🚨 QA Connection Failure: {e}")
        return None
