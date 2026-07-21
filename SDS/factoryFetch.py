
import requests

from SDS.auth_api import login_to_SDS_factory
from SDS.headers import build_token_headers
from SDS.time import get_dynamic_time_range, get_past_unfinished_time_range

PENDING = 1
ACCEPTED = 2
COMPLETED = 6
ACCPEPTED = ACCEPTED


def fetch_factory_order_records(status, time_range=None, page_size=10000, max_pages=100):
    url = "https://factory-api.sdspod.com/factory_orders/v2/order/allByEs"
    query_time_range = time_range or get_dynamic_time_range(days_before=2, days_after=1)
    factory_token = login_to_SDS_factory()
    if not factory_token:
        return []

    factory_headers = build_token_headers(factory_token)
    all_records = []

    try:
        for page in range(1, max_pages + 1):
            params = {
                "size": page_size,
                "page": page,
                "status": status,
                "noManuscriptFeedbackStatus": 1,
                "sort": "-id",
                **query_time_range
            }
            response = requests.get(url, params=params, headers=factory_headers)

            if response.status_code != 200:
                print(f"Server Error ({response.status_code}): {response.text}")
                return all_records

            records = response.json().get("records", [])
            all_records.extend(records)
            print(f"Fetched {len(records)} records from Factory API page {page}.")

            if len(records) < page_size:
                break

        return all_records

    except Exception as e:
        print(f"Connection error: {e}")
        return []


def fetch_factory_order_ids(status, time_range=None):
    records = fetch_factory_order_records(status, time_range=time_range)
    return [record.get("no") for record in records if record.get("no")]


def factory_fetch_records():
    return fetch_factory_order_ids(ACCEPTED)


def fetch_old_unfinished_order_ids(days_before=7):
    return fetch_factory_order_ids(
        ACCEPTED,
        time_range=get_past_unfinished_time_range(days_before=days_before)
    )
