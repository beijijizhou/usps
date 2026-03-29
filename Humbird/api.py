from urllib import response

import requests
import json

TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc1N1cGVyTWFuYWdlciI6ZmFsc2UsImdyb3VwSWQiOjIwMjQ1MTEzMSwicmVsVHlwZSI6Miwic2Vzc2lvbklkIjoiMjBlMmIxNWM1NTVhNGFkZjgyYTQyNzQ5MjZhZDlhNzMiLCJyZWxBcHBJZCI6MjU3MjY2OCwidXNlcklkIjoxMDA3NTAxLCJhcHBPcGVyYXRpb25QbGF0Zm9ybSI6ZmFsc2UsImNsaWVudFR5cGUiOjEsImFwcFR5cGUiOjEwMiwiYXBwSWQiOjI2MDI5NDcsInNjb3BlIjoiYWRtaW4iLCJ1c2VyVHlwZSI6OSwiaXNTVmlwIjp0cnVlLCJ1c2VybmFtZSI6IjI1NzI2NjhfMTg2NTAyODYwMjgifQ.hnNIJt7yOvv_HjH_Ovb1IOeFXPsQixVR8tuMGvsXyN4qh9fIwb2Xixr8BnKIcBzcvW8FlNkf0LB2pSj0P4wu8A"
get_order_nonce = "394266"
sign = "ebb10288176da7276905f20e00ef22c4dbea94166e26f758ddbea1cd1c9c7e4b"
stamp = "1774817820131"
headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh",
    "authorization": f"Bearer {TOKEN}",
    "content-type": "application/json;charset=UTF-8",
    "nonce": get_order_nonce,
    "sign": sign,
    "stamp": stamp,
    "priority": "u=1, i",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "referer": "https://flyshark.merchant.hihumbird.com/"
}


def fetch_humbird_page():
    url = "https://apigw.hihumbird.com/production/v1/production/order/item/page"

    # These headers MUST match your fetch call exactly

    # Use the RAW string from the "body" of your fetch
    # DO NOT convert this to a dictionary, or the 'sign' will definitely fail
    payload = '{"page":1,"page_size":20,"sum_total_qty":true,"status":["1"],"order_compositions":[],"process_route_ids":[],"order_third_status_list":[],"performance_status_list":[],"system_performance_status_list":[],"shipping_status_list":[],"order_source_list":[],"logistics_sorting_code_list":[],"styles":{"style_ids":[],"style_sku_ids":[]},"sort":[{"sort_by":"created","sort_type":2}]}'

    try:
        # We use data= instead of json= to keep the string minified (no spaces)
        response = requests.post(url, headers=headers,
                                 data=payload, timeout=10)
        print(f"API Request Sent. Status Code: {response}")
        if response.status_code == 200:
            data = response.json()
            records = data.get("data", {}).get("list", [])
            ids = [r.get("rel_id") for r in records if r.get("rel_id")]
            return ids
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None


def fetch_humbird_order_details():
    """
    Mimics the cURL for https://apigw.hihumbird.com/oc/v2/orders/list
    Args:
        order_ids (list): List of strings extracted from the Page API
    """
    get_tracking_nonce = "809348"  # This is the same nonce used in your cURL for the detail fetch
    get_tracking_stamp = "1774817820638"
    get_tracking_sign = "299be2e2841f4577c4ab2ecdae4fc92cb46702fc9e6e6b0e8a796f26e63ff9ed"
    # 1. EXACT Headers from your cURL
    # Note: These values (sign/nonce/stamp) are specific to the cURL body.
    # If the order_ids change significantly, the sign will likely fail.
    order_ids = fetch_humbird_page()

    # 2. Reconstruct the body structure
    payload = {
        "order_ids": order_ids,
        "query_field_list": ["third_detail"]
    }

    # 3. CRITICAL: Use separators to remove all whitespace (Minify)
    # This ensures the string sent to the server matches the signature's calculation

    try:
        # Use data= instead of json= to prevent Requests from adding spaces
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh",
            "authorization": f"Bearer {TOKEN}",
            "content-type": "application/json;charset=UTF-8",
            "nonce": get_tracking_nonce,
            "sign": get_tracking_sign,
            "stamp": get_tracking_stamp,
            "Referer": "https://flyshark.merchant.hihumbird.com/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        }
        payload_new = json.dumps(payload, separators=(',', ':'))  # Minify JSON
       
# THE ACTUAL CALL
        response = requests.post(
            "https://apigw.hihumbird.com/oc/v2/orders/list",
            headers=headers,
            data=payload_new  # Use 'data' for raw strings
        )
        if response.status_code == 200:
            
            return response.json()
        else:
            print(f"Failed! Status: {response.status_code}")
            print(f"Server Message: {response.text}")
            return None
    except Exception as e:
        print(f"Request Exception: {e}")
        return None
