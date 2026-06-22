
import requests

from SDS.auth_api import login_to_SDS_factory
from SDS.time import get_dynamic_time_range
import config
PENDING = 1
ACCPEPTED = 2

def factory_fetch_records():
    url = "https://factory-api.sdspod.com/factory_orders/v2/order/allByEs"
    time_range = get_dynamic_time_range(days_before=2, days_after=1)
    params = {
        "size": 500,
        "page": 1,
        "status": ACCPEPTED,  # Only fetch orders with status=1 (Pending)
        "noManuscriptFeedbackStatus": 1,
        "sort": "-id",
        **time_range
    }
    # YD_Factory_TOKEN = "sds-factory:2ea30cef-776c-48dc-b674-dc7c9434cef3"
    
   
    factory_token = login_to_SDS_factory()

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
