import requests
import re
from datetime import datetime, timedelta

# Hard-coded Token
AUTH_TOKEN = "a2d870e2-1846-41b6-ae61-5373336f4b7c"

def get_dynamic_time_range(days_before=1, days_after=1):
    """Calculates startTime and endTime for the API params."""
    now = datetime.now()
    start_dt = (now - timedelta(days=days_before)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = (now + timedelta(days=days_after)).replace(hour=23, minute=59, second=59, microsecond=0)
    return {
        "startTime": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "endTime": end_dt.strftime("%Y-%m-%d %H:%M:%S")
    }

def get_label_data(label_no):
    """Background engine for the Riin API call."""
    url = "https://tshirt.riin.com/manufacture/deliverGoodsLabel/scan/labelNo"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": AUTH_TOKEN,
        "referer": "https://tshirt.riin.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
        "x-requested-with": "XMLHttpRequest"
    }
    cookies = {"authorized-token-FACTORY": AUTH_TOKEN}
    params = {"labelNo": label_no.strip()}
    
    try:
        return requests.get(url, headers=headers, cookies=cookies, params=params, timeout=15)
    except Exception as e:
        return str(e)