from SDS.factoryFetch import PENDING, fetch_factory_order_ids, fetch_old_unfinished_order_ids
from SDS.pre_scan import DEFAULT_MAX_WORKERS, run_parallel_scan_generator


def fetch_unproduced_order_ids():
    return fetch_factory_order_ids(PENDING)


def fetch_unproduced_orders_with_tracking(max_workers=DEFAULT_MAX_WORKERS, on_progress=None, order_ids=None):
    order_ids = order_ids if order_ids is not None else fetch_unproduced_order_ids()
    rows = []
    total = len(order_ids)

    for index, res in enumerate(run_parallel_scan_generator(order_ids, max_workers=max_workers), start=1):
        rows.append(format_tracking_preview_row(res))
        if on_progress:
            on_progress(index, total, res)

    return order_ids, rows


def fetch_old_unfinished_orders_with_tracking(days_before=7, max_workers=DEFAULT_MAX_WORKERS, on_progress=None):
    order_ids = fetch_old_unfinished_order_ids(days_before=days_before)
    return fetch_unproduced_orders_with_tracking(
        max_workers=max_workers,
        on_progress=on_progress,
        order_ids=order_ids
    )


def format_tracking_preview_row(scan_result):
    tracking_number = scan_result.get("tracking", "")
    return {
        "Order ID": scan_result.get("Order ID", ""),
        "Tracking Number": tracking_number,
        "Carrier": scan_result.get("carrier", ""),
        "Status": "已找到" if tracking_number else scan_result.get("msg", "")
    }
