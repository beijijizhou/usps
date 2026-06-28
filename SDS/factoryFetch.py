
import requests

from SDS.auth_api import login_to_SDS_factory
from SDS.headers import build_token_headers
from SDS.time import get_dynamic_time_range

PENDING = 1
ACCEPTED = 2
ACCPEPTED = ACCEPTED

def fetch_factory_order_ids(status):
    url = "https://factory-api.sdspod.com/factory_orders/v2/order/allByEs"
    time_range = get_dynamic_time_range(days_before=2, days_after=1)
    params = {
        "size": 10000,
        "page": 1,
        "status": status,
        "noManuscriptFeedbackStatus": 1,
        "sort": "-id",
        **time_range
    }

    factory_token = login_to_SDS_factory()
    factory_headers = build_token_headers(factory_token)

    try:
        response = requests.get(url, params=params, headers=factory_headers)

        if response.status_code == 200:
            records = response.json().get("records", [])
            print(f"Fetched {len(records)} records from Factory API.")
            return [record.get("no") for record in records if record.get("no")]

        print(f"Server Error ({response.status_code})")
        return []

    except Exception as e:
        print(f"Connection error: {e}")
        return []


def factory_fetch_records():
    return fetch_factory_order_ids(ACCEPTED)
