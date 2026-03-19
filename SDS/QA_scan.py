import requests
import time

QA_token ="sds-pod:4a120912-6ced-4d77-80b0-a125d16daf6a"

factory_headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Cookie": "PASTE_YOUR_ACTUAL_COOKIE_STRING_HERE",
    "access-token":QA_token,
}
def scanID(order_no):
    """
    Tests the QC API for a specific order number.
    """
    url = "https://pod-api.sdspod.com/pod/qc/factoryOrder/fast"   
    # Generate the 't' timestamp in milliseconds
    timestamp_ms = int(time.time() * 1000)
    
    params = {
        "no": order_no,
        "t": timestamp_ms
    }

    try:
        print(f"\nScanning Order: {order_no}...")
        r = requests.get(url, params=params, headers=factory_headers, timeout=10)
        
        if r.status_code == 200:
            qc_data = r.json()
            print(f"QC Data Received: {qc_data}")
            return qc_data
        else:
            print(f"QC API Error {r.status_code}: {r.text}")
            return None
            
    except Exception as e:
        print(f"Scan failed: {e}")
        return None

# --- Testing Block ---
def run_batch_scan(ids):
    scan_results = []
    print(f"Starting batch scan for {len(ids)} orders...")
    
    for i, order_no in enumerate(ids, 1):
        # Call your existing scanID function
        result = scanID(order_no)
        
        if result:
            scan_results.append({"order_no": order_no, "data": result})
            print(f"[{i}/{len(ids)}] Successfully scanned {order_no}")
        else:
            print(f"[{i}/{len(ids)}] Failed to scan {order_no}")
            
    return scan_results

# if __name__ == "__main__":
#     all_data = run_batch_scan(order_ids)
#     print(f"\nBatch Complete. Scanned {len(all_data)} items.")


