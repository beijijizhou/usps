# usps_utils.py
import requests

def get_access_token(client_id, client_secret):
    url = "https://apis.usps.com/oauth2/v3/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("access_token")

def track_packages(token, tracking_numbers):
    url = "https://apis.usps.com/tracking/v3r2/tracking"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = [{"trackingNumber": str(tn).strip()} for tn in tracking_numbers if tn.strip()]
    response = requests.post(url, json=payload, headers=headers)
    return response.json()