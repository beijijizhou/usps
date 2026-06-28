from SDS.factoryFetch import PENDING, fetch_factory_order_ids
from SDS.pre_scan import run_parallel_scan_generator


def fetch_unproduced_order_ids():
    return fetch_factory_order_ids(PENDING)


def fetch_unproduced_orders_with_tracking():
    order_ids = fetch_unproduced_order_ids()
    rows = []

    for res in run_parallel_scan_generator(order_ids):
        rows.append(format_tracking_preview_row(res))

    return order_ids, rows


def format_tracking_preview_row(scan_result):
    tracking_number = scan_result.get("tracking", "")
    return {
        "Order ID": scan_result.get("Order ID", ""),
        "Tracking Number": tracking_number,
        "Carrier": scan_result.get("carrier", ""),
        "Status": "Found" if tracking_number else scan_result.get("msg", "")
    }
