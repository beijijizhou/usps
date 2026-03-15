import requests
import streamlit as st
from courier.base_courier import BaseCourier

class UspsCourier(BaseCourier):
    def __init__(self):
        self.client_id = st.secrets["USPS_CLIENT_ID"]
        self.client_secret = st.secrets["USPS_CLIENT_SECRET"]

    def _get_token(self):
        url = "https://apis.usps.com/oauth2/v3/token"
        payload = {"grant_type": "client_credentials", "client_id": self.client_id, "client_secret": self.client_secret}
        return requests.post(url, json=payload).json().get("access_token")

    def track(self, tracking_number_list, order_map=None):
        token = self._get_token()
        url = "https://apis.usps.com/tracking/v3r2/tracking"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = [{"trackingNumber": str(n).strip()} for n in tracking_number_list]
        
        try:
            resp = requests.post(url, json=payload, headers=headers).json()
            results = []
            packages = resp if isinstance(resp, list) else []
            
            for package in packages:
                num = package.get('trackingNumber')
                events = package.get('trackingEvents', [])
                order_id = self.order_map.get(num, "N/A")
                # Standardized Extraction Logic
                city, state, zip_c, last_time = "N/A", "N/A", "N/A", "N/A"
                
                if events:
                    latest = events[0]
                    city = latest.get('eventCity', 'N/A')
                    state = latest.get('eventState', 'N/A')
                    zip_c = latest.get('eventZIPCode', 'N/A')
                    raw_time = latest.get('eventDateTime') or latest.get('eventTimestamp') or "N/A"
                    if raw_time != "N/A":
                        last_time = raw_time.replace('T', ' ').split('.')[0].replace('Z', '')

                results.append({
                    "Order ID": order_id,
                    "Tracking Number": num,
                    "Status": package.get('status', 'Unknown'),
                    "Last Updated": last_time,
                    "Location": f"{city}, {state} {zip_c}"
                })
        except:
            return []