import requests

from SDS.time import get_dynamic_time_range
PENDING = 1
ACCPEPTED = 2

def factory_fetch_records():
    url = "https://factory-api.sdspod.com/factory_orders/v2/order/allByEs"
    time_range = get_dynamic_time_range(days_before=0, days_after=1)
    params = {
        "size": 500,
        "page": 1,
        "status": PENDING,  # Only fetch orders with status=1 (Pending)
        "noManuscriptFeedbackStatus": 1,
        "sort": "-id",
        **time_range
    }

    factory_token = "sds-factory:5024fbff-fe8e-464a-8bee-e7223d84fc44"

    factory_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "access-token": factory_token
    }

    try:
        response = requests.get(url, params=params, headers=factory_headers)

        if response.status_code == 200:
            data = response.json()
            # print(data)
            # print(len(data.get("records", [])))
            records = data.get("records", [])
            print(f"Fetched {len(records)} records from Factory API.")
            # Extract just the 'no' fields into a list
            order_numbers = [record.get("no")
                             for record in records if record.get("no")]
            return order_numbers
        else:
            print(f"Server Error ({response.status_code})")
            return []

    except Exception as e:
        print(f"Connection error: {e}")
        return []
