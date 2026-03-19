import requests

def factory_fetch_records():
    url = "https://factory-api.sdspod.com/factory_orders/v2/order/allByEs"

    params = {
        "size": 500,
        "page": 1,
        "status": 2,
        "noManuscriptFeedbackStatus": 1,
        "startTime": "2026-02-18 00:00:00",
        "endTime": "2026-03-17 23:59:59",
        "sort": "-id"
    }

    factory_token = "sds-factory:b738d31b-e72f-486d-9d1a-4e03a372424f"

    factory_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*", 
        "access-token": factory_token
    }

    try:
        response = requests.get(url, params=params, headers=factory_headers)
        
        if response.status_code == 200:
            data = response.json()
            records = data.get("records", [])
            
            # Extract just the 'no' fields into a list
            order_numbers = [record.get("no") for record in records if record.get("no")]
            return order_numbers
        else:
            print(f"Server Error ({response.status_code})")
            return []
            
    except Exception as e:
        print(f"Connection error: {e}")
        return []
