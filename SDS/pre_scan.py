import requests
import time
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "access-token": "sds-pod:38b7d608-33d6-485c-b3b0-3c5eb348e5e6"
    }

def process_single_order(order_no):
    """The full chain for one ID: Order No -> Factory ID -> Tracking No"""
    order_no = str(order_no).strip()
    try:
        # Step 1: Get Factory ID
        f_url = "https://pod-api.sdspod.com/pod/qc/factoryOrder"
        f_res = requests.get(f_url, params={"no": order_no, "t": int(time.time()*1000)}, 
                             headers=get_headers(), timeout=100)
        print(get_headers())
        factory_id = f_res.json().get("orderId") if f_res.status_code == 200 else None
        print(f"Order {order_no} -> Factory ID: {factory_id}")
        if not factory_id:
            return {"Order ID": order_no, "status": "error", "msg": "Factory ID not found"}

        # Step 2: Get Tracking
        t_url = f"https://pod-api.sdspod.com/pod/parcel/qc/{factory_id}/detail"
        t_res = requests.get(t_url, params={"t": int(time.time()*1000)}, 
                             headers=get_headers(), timeout=100)
        
        if t_res.status_code == 200:
            details = t_res.json().get("detailList", [])
            parcel = details[0]
            return {
                    "Order ID": order_no, 
                    "status": "success", 
                    "tracking": parcel.get("carriageNo"),
                    "carrier": parcel.get("carriageName", "").upper() # e.g., "USPS"
                }
        
        return {"Order ID": order_no, "status": "error", "msg": "No parcel details"}
    except Exception as e:
        return {"Order ID": order_no, "status": "error", "msg": str(e)}

from concurrent.futures import ThreadPoolExecutor, as_completed

def run_parallel_scan_generator(order_ids, max_workers=8):
    """
    Engine: Executes API calls in parallel and yields results immediately.
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Map each order_id to a thread task
        future_to_order = {
            executor.submit(process_single_order, str(no).strip()): no 
            for no in order_ids
        }
        
        # As soon as ANY thread finishes, yield its result back to the UI
        for future in as_completed(future_to_order):
            try:
                yield future.result()
            except Exception as e:
                # Fallback if the thread itself crashes
                order_id = future_to_order[future]
                yield {"Order ID": order_id, "status": "error", "msg": str(e)}