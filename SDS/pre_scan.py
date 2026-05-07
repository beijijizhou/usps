import requests
import time
QA_token = "sds-pod:38b7d608-33d6-485c-b3b0-3c5eb348e5e6"
headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "access-token":  QA_token# Use your actual token variable
    }
def run_batch_pre_scan(ids):
    scan_results = []
    print(f"Starting batch scan for {len(ids)} orders...")
    
    for i, order_no in enumerate(ids, 1):
        # Call your existing scanID function
        result = get_factory_order_id(order_no)
        
        if result:
            scan_results.append({"order_no": order_no, "data": result})
            print(f"[{i}/{len(ids)}] Successfully scanned {order_no}")
        else:
            print(f"[{i}/{len(ids)}] Failed to scan {order_no}")
            
    return scan_results

def get_factory_order_id(order_no):
    """
    Fetches the internal Factory Order ID (e.g., 906204887704313856) 
    using the Order Number (e.g., 2006820000273516).
    """
    url = "https://pod-api.sdspod.com/pod/qc/factoryOrder"
    timestamp_ms = int(time.time() * 1000)
    
    params = {
        "no": order_no,
        "t": timestamp_ms
    }
    
    # Using the same headers you defined for your other SDS functions
   

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Extract the orderId from the response body
            # Based on your example, it is inside the top-level JSON
            factory_id = data.get("orderId")
            
            if factory_id:
                return factory_id
            else:
                print(f"Key 'orderId' not found in response for {order_no}")
                return None
        else:
            print(f"API Error {response.status_code} for {order_no}")
            return None
            
    except Exception as e:
        print(f"Request failed for {order_no}: {e}")
        return None
    
    
def get_tracking_from_factory_id(factory_order_id):
    """
    Calls the detail endpoint using the long Factory Order ID
    and extracts the carriageNo (Tracking Number).
    """
    # The ID is part of the URL path in this API
    url = f"https://pod-api.sdspod.com/pod/parcel/qc/{factory_order_id}/detail"
    timestamp_ms = int(time.time() * 1000)
    
    params = {"t": timestamp_ms}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Navigate the JSON: detailList is a list of parcels
            detail_list = data.get("detailList", [])
            
            if detail_list and len(detail_list) > 0:
                # Get the tracking number (carriageNo) from the first parcel
                tracking_no = detail_list[0].get("carriageNo")
                return tracking_no
            else:
                print(f"No parcels found in detailList for {factory_order_id}")
                return None
        else:
            return None
            
    except Exception as e:
        print(f"Tracking fetch failed: {e}")
        return None