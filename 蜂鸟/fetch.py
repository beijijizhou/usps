import requests
import json

def fetch_humbird_orders(token, page=1, page_size=200):
    """
    Fetches order data from the Humbird production API.
    Returns the JSON response or None if the request fails.
    """
    url = "https://apigw.hihumbird.com/production/v1/production/order/item/page"
    
    headers = {
        "Authorization": token if token.startswith("Bearer ") else f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://www.hihumbird.com",
        "Referer": "https://www.hihumbird.com/"
    }
    
    payload = {
        "page": page,
        "page_size": page_size,
        "sum_total_qty": True,
        "status": ["1"],
        "order_compositions": [],
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

    try:
        response = requests.post(url, json=payload, headers=headers)
        
        # Check for HTTP errors (401, 403, 500, etc.)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    
    return None

# ==========================================
# TEST BLOCK
# ==========================================
if __name__ == "__main__":
    # Replace with your actual token for testing
    TEST_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc1N1cGVyTWFuYWdlciI6ZmFsc2UsImdyb3VwSWQiOjIwMjQ1MTEzMSwicmVsVHlwZSI6Miwic2Vzc2lvbklkIjoiMjNlOTE2MTk2NWUzNDZiNTk5N2JiMzM5NmY5NGQyYzQiLCJyZWxBcHBJZCI6MjU3MjY2OCwidXNlcklkIjoxMDA3NTAxLCJhcHBPcGVyYXRpb25QbGF0Zm9ybSI6ZmFsc2UsImNsaWVudFR5cGUiOjEsImFwcFR5cGUiOjEwMiwiYXBwSWQiOjI2MDI5NDcsInNjb3BlIjoiYWRtaW4iLCJ1c2VyVHlwZSI6OSwiaXNTVmlwIjp0cnVlLCJ1c2VybmFtZSI6IjI1NzI2NjhfMTg2NTAyODYwMjgifQ.cmm4yvcYvQNxXutqgKR9yOk4B1zxUeZYSosID6J96zY7xal_QQd-kURgHOOSra5RN731DI1bpleEfd5mLOAmTQ" 

    print("Testing Humbird API Fetch...")
    result = fetch_humbird_orders(TEST_TOKEN)

    if result:
        print("Successfully connected to API.")
        
        # Drill down into the data structure
        # Typical Humbird structure is result['data']['list']
        data_content = result.get("data", {})
        order_list = data_content.get("list", [])
        
        print(f"Total items found in this page: {len(order_list)}")
        
        if order_list:
            print("\nFirst Item Sample:")
            # Print the first item formatted nicely so you can see the keys
            print(json.dumps(order_list[0], indent=2))
        else:
            print("Request successful, but the order list is empty.")
    else:
        print("Failed to fetch data. Check your Token or Network connection.")