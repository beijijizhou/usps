import requests
import json

# 1. URL from your trace
URL = "https://apigw.hihumbird.com/oc/v2/orders/list"

# 2. Headers exactly as they appear in Postman
HEADERS = {
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc1N1cGVyTWFuYWdlciI6ZmFsc2UsImdyb3VwSWQiOjIwMjQ2MjM3MiwicmVsVHlwZSI6Miwic2Vzc2lvbklkIjoiMDliMGE0ZWMyNDVjNGE2MmE4YTQyNjNkYTIxMzk0NTAiLCJyZWxBcHBJZCI6MjYxNDA2OCwidXNlcklkIjoxMDM0MjI1LCJhcHBPcGVyYXRpb25QbGF0Zm9ybSI6ZmFsc2UsImNsaWVudFR5cGUiOjEsImFwcFR5cGUiOjEwMiwiYXBwSWQiOjI2MTQwNzAsInNjb3BlIjoiYWRtaW4iLCJ1c2VyVHlwZSI6OSwiaXNTVmlwIjp0cnVlLCJ1c2VybmFtZSI6ImhhbG9vcG9kXzE4MTU3Nzc0NjI3In0.1VhsxMiwzMPxuOelBLbCN6yxpTCj4YM8PPAHiL3ogWl0qGeTbnVsezMPr5f7VnOus91EoL2qf4ATGH9Iz9LXOA",
    "Content-Type": "application/json;charset=UTF-8",
    "nonce": "431737",
    "sign": "99426e2f12dd0dd1f0e7dff114ea227151b5e3a0aa133093b800219f76970b2f",
    "stamp": "1770683541273",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://haloopod.merchant.hihumbird.com",
    "Referer": "https://haloopod.merchant.hihumbird.com/"
}

# 3. The Payload (Dictionary converted to JSON)
# Make sure this matches what you put in Postman EXACTLY.
payload = {
    "page": 1,
    "page_size": 20,
    "sum_total_qty": True,
    "status": [],
    "order_compositions": [],
    "created_range": {
        "from": 1762923600478,
        "to": 1770699599478
    },
    "logistics_sorting_code_list": [],
    "order_source_list": [],
    "order_third_status_list": [],
    "performance_status_list": [],
    "process_route_ids": [],
    "shipping_status_list": [],
    "sort": [{"sort_by": "created", "sort_type": 2}],
    "styles": {"style_ids": [], "style_sku_ids": []},
    "system_performance_status_list": []
}

compact_json_body = json.dumps(payload, separators=(',', ':'))

def fetch_data():
    # We send compact_json_body as 'data'
    response = requests.post(URL, headers=HEADERS, data=compact_json_body)
    
    if response.status_code == 200:
        print("✅ Python is now matching Postman!")
        print(response.json())
    else:
        print(f"❌ Failed. Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    fetch_data()