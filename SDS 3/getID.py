import requests
import time
url = "https://factory-api.sdspod.com/factory_orders/v2/order/allByEs"
# https://factory-api.sdspod.com/factory_orders/v2/order/allByEs?size=50&page=1&status=1&noManuscriptFeedbackStatus=1&startTime=2026-02-15%2000%3A00%3A00&endTime=2026-03-15%2023%3A59%3A59&sort=-id
# Updated parameters based on your new request
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
# Add these headers (Copy the actual values from your browser)
factory_headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Cookie": "PASTE_YOUR_ACTUAL_COOKIE_STRING_HERE",
    "access-token":factory_token
}

def fetch_records():
    try:
        r = requests.get(url, params=params, headers=factory_headers, timeout=10)
        
        if r.status_code != 200:
            print(f"Error {r.status_code}: {r.text}")
            return []
            
        r.raise_for_status()
        data = r.json()
        
        records = data.get("records", [])
        print(f"Total Records: {len(records)}")
        
        for record in records:
            print(record.get("no", "N/A"))
            
        return records
        
    except Exception as e:
        print(f"Failed: {e}")
        return []
QA_token ="sds-pod:3ccf8e26-451c-4ce2-85ed-1284b3123db8"

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
order_ids = [
    "2009900000001399", "2009900000001398", "2009900000001395", "2009900000001386",
    "2009900000001385", "2009900000001370", "2009900000001336", "2009900000001335",
    "2009900000001328", "2009900000001327", "2009900000001326", "2009900000001314",
    "2009900000001313", "2009900000001305", "2009900000001304", "2009900000001302",
    "2009900000001301", "2009900000001300", "2009900000001299", "2009900000001298",
    "2009900000001297", "2009900000001296", "2009900000001295", "2009900000001294",
    "2009900000001293", "2009900000001292", "2009900000001291", "2009900000001290",
    "2009900000001289", "2009900000001288", "2009900000001287", "2009900000001286",
    "2009900000001285", "2009900000001284", "2009900000001283", "2009900000001282",
    "2009900000001281", "2009900000001280", "2009900000001279", "2009900000001278",
    "2009900000001277", "2009900000001276", "2009900000001274", "2009900000001273",
    "2009900000001272", "2009900000001271", "2009900000001270", "2009900000001269",
    "2009900000001268", "2009900000001267", "2009900000001266", "2009900000001265",
    "2009900000001264", "2009900000001263", "2009900000001262", "2009900000001259",
    "2009900000001257", "2009900000001255", "2009900000001254", "2009900000001253",
    "2009900000001251", "2009900000001250", "2009900000001248", "2009900000001245",
    "2009900000001244", "2009900000001241", "2009900000001240", "2009900000001239",
    "2009900000001236", "2009900000001234", "2009900000001232", "2009900000001231",
    "2009900000001230", "2009900000001229", "2009900000001227", "2009900000001226",
    "2009900000001225", "2009900000001224", "2009900000001223", "2009900000001221",
    "2009900000001219", "2009900000001217", "2009900000001216", "2009900000001215",
    "2009900000001213", "2009900000001212", "2009900000001211", "2009900000001210",
    "2009900000001209", "2009900000001208", "2009900000001207", "2009900000001206",
    "2009900000001205", "2009900000001203", "2009900000001200", "2009900000001197",
    "2009900000001195"
]
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

if __name__ == "__main__":
    all_data = run_batch_scan(order_ids)
    print(f"\nBatch Complete. Scanned {len(all_data)} items.")