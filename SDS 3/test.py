import requests
import time  # Added to handle rate limiting
from getID import scanID

url = "https://factory-api.sdspod.com/factory_orders/v2/order/allByEs"

params = {
    "size": 200,
    "page": 1,
    "status": 2,
    "noManuscriptFeedbackStatus": 1,
    "startTime": "2026-02-15 00:00:00",
    "endTime": "2026-03-15 23:59:59",
    "sort": "-id"
}

factory_token = "sds-factory:1977ffbb-8906-49ba-9233-1a5f6cd57dfa"

factory_headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Cookie": "YOUR_ACTUAL_COOKIE_HERE", 
    "access-token": factory_token
}

def fetch_records():
    try:
        response = requests.get(url, params=params, headers=factory_headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Server Error ({response.status_code}): {response.text}")
            return []

        data = response.json()
        records = data.get("records", [])
        
        # 1. Extract the 'no' field
        order_numbers = [record.get("no") for record in records if record.get("no")]
        total = len(order_numbers)
        print(f"--- Starting Batch Scan of {total} items ---")
        
        # 2. Loop through and scan one by one
        for index, order_no in enumerate(order_numbers, 1):
            print(f"[{index}/{total}] Scanning: {order_no}")
            
            try:
                scanID(order_no)
                # Optional: print(f"Successfully scanned: {order_no}")
            except Exception as scan_err:
                print(f"Error scanning {order_no}: {scan_err}")

            # 3. Add a small pause (0.1s) if the server starts blocking you
            # time.sleep(0.1) 
        
        return order_numbers

    except Exception as e:
        print(f"Connection error: {e}")
        return []

if __name__ == "__main__":
    fetch_records()