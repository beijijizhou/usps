from urllib import response

import requests
import json

TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc1N1cGVyTWFuYWdlciI6ZmFsc2UsImdyb3VwSWQiOjIwMjQ1MTEzMSwicmVsVHlwZSI6Miwic2Vzc2lvbklkIjoiNGY1ZjNmOWQyYjUxNDU2YmJiZjFkMGVmYmU5ZThlZWUiLCJyZWxBcHBJZCI6MjU3MjY2OCwidXNlcklkIjoxMDA3NTAxLCJhcHBPcGVyYXRpb25QbGF0Zm9ybSI6ZmFsc2UsImNsaWVudFR5cGUiOjEsImFwcFR5cGUiOjEwMiwiYXBwSWQiOjI2MDI5NDcsInNjb3BlIjoiYWRtaW4iLCJ1c2VyVHlwZSI6OSwiaXNTVmlwIjp0cnVlLCJ1c2VybmFtZSI6IjI1NzI2NjhfMTg2NTAyODYwMjgifQ.oBOuBw369370G9KVt9iGShwuPPAx3SbabPTcYkQmySS8auHUnToXeNqK2UlWL0dqHRoyaX_wCG7SzW6J0PpmJA"
headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh",
    "authorization": f"Bearer {TOKEN}",
    "content-type": "application/json;charset=UTF-8",
    "nonce": "567744",
    "sign": "fc5d70330cc21ca0200492f4fd4e40b918f79624aef3f405ac8866e1a98710ae",
    "stamp": "1774581689141",
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
            ids = [r.get("id") for r in records if r.get("id")]
            return ids
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None


def fetch_humbird_order_details(order_ids):
    """
    Mimics the cURL for https://apigw.hihumbird.com/oc/v2/orders/list
    Args:
        order_ids (list): List of strings extracted from the Page API
    """
    url = "https://apigw.hihumbird.com/oc/v2/orders/list"

    # 1. EXACT Headers from your cURL
    # Note: These values (sign/nonce/stamp) are specific to the cURL body.
    # If the order_ids change significantly, the sign will likely fail.
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh',
        'authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc1N1cGVyTWFuYWdlciI6ZmFsc2UsImdyb3VwSWQiOjIwMjQ1MTEzMSwicmVsVHlwZSI6Miwic2Vzc2lvbklkIjoiNGY1ZjNmOWQyYjUxNDU2YmJiZjFkMGVmYmU5ZThlZWUiLCJyZWxBcHBJZCI6MjU3MjY2OCwidXNlcklkIjoxMDA3NTAxLCJhcHBPcGVyYXRpb25QbGF0Zm9ybSI6ZmFsc2UsImNsaWVudFR5cGUiOjEsImFwcFR5cGUiOjEwMiwiYXBwSWQiOjI2MDI5NDcsInNjb3BlIjoiYWRtaW4iLCJ1c2VyVHlwZSI6OSwiaXNTVmlwIjp0cnVlLCJ1c2VybmFtZSI6IjI1NzI2NjhfMTg2NTAyODYwMjgifQ.oBOuBw369370G9KVt9iGShwuPPAx3SbabPTcYkQmySS8auHUnToXeNqK2UlWL0dqHRoyaX_wCG7SzW6J0PpmJA',
        'content-type': 'application/json;charset=UTF-8',
        'nonce': '484203',
        'origin': 'https://flyshark.merchant.hihumbird.com',
        'priority': 'u=1, i',
        'referer': 'https://flyshark.merchant.hihumbird.com/',
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'sign': '543091f43c36e0d137dcaa55a69975026a6382fcf6fa4ed217427740ed026670',
        'stamp': '1774584236121',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
    }

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
            "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc1N1cGVyTWFuYWdlciI6ZmFsc2UsImdyb3VwSWQiOjIwMjQ1MTEzMSwicmVsVHlwZSI6Miwic2Vzc2lvbklkIjoiNGY1ZjNmOWQyYjUxNDU2YmJiZjFkMGVmYmU5ZThlZWUiLCJyZWxBcHBJZCI6MjU3MjY2OCwidXNlcklkIjoxMDA3NTAxLCJhcHBPcGVyYXRpb25QbGF0Zm9ybSI6ZmFsc2UsImNsaWVudFR5cGUiOjEsImFwcFR5cGUiOjEwMiwiYXBwSWQiOjI2MDI5NDcsInNjb3BlIjoiYWRtaW4iLCJ1c2VyVHlwZSI6OSwiaXNTVmlwIjp0cnVlLCJ1c2VybmFtZSI6IjI1NzI2NjhfMTg2NTAyODYwMjgifQ.oBOuBw369370G9KVt9iGShwuPPAx3SbabPTcYkQmySS8auHUnToXeNqK2UlWL0dqHRoyaX_wCG7SzW6J0PpmJA",
            "content-type": "application/json;charset=UTF-8",
            "nonce": "484203",
            "sign": "543091f43c36e0d137dcaa55a69975026a6382fcf6fa4ed217427740ed026670",
            "stamp": "1774584236121",
            "Referer": "https://flyshark.merchant.hihumbird.com/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        }
        payload_raw = '{"order_ids":["888199380862025217","888199389485579777","888199385937198593","888199398838812161","888199374251802113","888199377389141505","888199376139238913","888199379041762817","888199382648864257","888199404752879105","888199401657482753","888199391113002497","888199387422014978","888199397303795201","888199384385338881","888199403184111105","888199406162066945","888199392295697921","888199393948319233","888199395592486401"],"query_field_list":["third_detail"]}'

# THE ACTUAL CALL
        response = requests.post(
            "https://apigw.hihumbird.com/oc/v2/orders/list",
            headers=headers,
            data=payload_raw  # Use 'data' for raw strings
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
