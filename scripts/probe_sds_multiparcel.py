import json
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import requests

from SDS.factoryFetch import ACCEPTED, fetch_factory_order_records
from SDS.headers import get_qa_headers
from SDS.time import get_past_unfinished_time_range


FACTORY_ORDER_URL = "https://pod-api.sdspod.com/pod/qc/factoryOrder"
PARCEL_DETAIL_URL = "https://pod-api.sdspod.com/pod/parcel/qc/{order_id}/detail"


def get_factory_order_id(order_no, headers):
    response = requests.get(
        FACTORY_ORDER_URL,
        params={"no": order_no, "t": int(time.time() * 1000)},
        headers=headers,
        timeout=(5, 20),
    )
    if response.status_code != 200:
        return None
    return response.json().get("orderId")


def get_parcel_detail(factory_order_id, headers):
    response = requests.get(
        PARCEL_DETAIL_URL.format(order_id=factory_order_id),
        params={"t": int(time.time() * 1000)},
        headers=headers,
        timeout=(5, 30),
    )
    if response.status_code != 200:
        return []
    return response.json().get("detailList", [])


def summarize_parcel(parcel):
    return {
        "parcelId": parcel.get("parcelId"),
        "parcelName": parcel.get("parcelName"),
        "carriageNo": parcel.get("carriageNo"),
        "carriageName": parcel.get("carriageName"),
        "pdfUrl": parcel.get("pdfUrl"),
        "laberPdf": parcel.get("laberPdf"),
        "status": parcel.get("status"),
        "scanFormStatus": parcel.get("scanFormStatus"),
        "keys": sorted(parcel.keys()),
    }


def main():
    records = fetch_factory_order_records(
        ACCEPTED,
        time_range=get_past_unfinished_time_range(days_before=1),
        page_size=200,
        max_pages=1,
    )
    headers = get_qa_headers()
    multi_parcel_orders = []
    factory_record_summary = []

    for record in records[:200]:
        order_no = record.get("no")
        if not order_no:
            continue
        factory_record_summary.append({
            "order_no": order_no,
            "keys": sorted(record.keys()),
            "quantity_fields": {
                key: record.get(key)
                for key in sorted(record.keys())
                if any(token in key.lower() for token in ["qty", "quantity", "count", "num"])
            },
            "maybe_item_fields": {
                key: type(record.get(key)).__name__
                for key in sorted(record.keys())
                if isinstance(record.get(key), (list, dict))
            },
        })
        factory_order_id = get_factory_order_id(order_no, headers)
        if not factory_order_id:
            continue
        parcels = get_parcel_detail(factory_order_id, headers)
        if len(parcels) > 1:
            multi_parcel_orders.append({
                "order_no": order_no,
                "factory_order_id": factory_order_id,
                "parcel_count": len(parcels),
                "parcels": [summarize_parcel(parcel) for parcel in parcels],
            })
        if len(multi_parcel_orders) >= 5:
            break

    print(json.dumps({
        "checked_records": min(len(records), 200),
        "multi_parcel_found": len(multi_parcel_orders),
        "factory_record_examples": factory_record_summary[:5],
        "examples": multi_parcel_orders,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
