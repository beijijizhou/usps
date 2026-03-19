import requests

def push_delivery_print(order_code):
    """
    Sends a POST request to goodsDeliveryPrint with the order code payload.
    """
    url = "https://factory.s2bdiy.com/req/factory/delivery/goodsDeliveryPrint"
    
    # Your Bearer Token
    bearer_token = "852457|c7MWRubJVYYQ9AoisDzRRZWuKr53k4O8ESbjnWbS"
    # bearer_token = "853860|2I68kVWFcn1x426A9oGQDrUbwWyFblB1vF1sNikh"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }

    # The payload (body) of the POST request
    payload = {
        "code": order_code
    }

    try:
        print(f"Pushing Delivery Print for code: {order_code}...")
        # Use requests.post for endpoints requiring a payload
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data}")
            return data
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"Failed to push {order_code}: {e}")
        return None

# --- Example Usage ---
if __name__ == "__main__":
    # Test with the code you provided
    push_delivery_print("TYLX97")