from SDS.factoryFetch import PENDING, ACCEPTED, fetch_factory_order_ids, fetch_factory_order_records
from SDS.pre_scan import DEFAULT_MAX_WORKERS, run_parallel_scan_generator
from SDS.time import get_past_unfinished_time_range


def fetch_unproduced_order_ids():
    return fetch_factory_order_ids(PENDING)


def fetch_unproduced_orders_with_tracking(max_workers=DEFAULT_MAX_WORKERS, on_progress=None, order_ids=None, record_by_order_id=None):
    order_ids = order_ids if order_ids is not None else fetch_unproduced_order_ids()
    record_by_order_id = record_by_order_id or {}
    rows = []
    total = len(order_ids)

    for index, res in enumerate(run_parallel_scan_generator(order_ids, max_workers=max_workers), start=1):
        rows.append(format_tracking_preview_row(
            res,
            record=record_by_order_id.get(res.get("Order ID"), {})
        ))
        if on_progress:
            on_progress(index, total, res)

    return order_ids, rows


def fetch_old_unfinished_orders_with_tracking(days_before=7, max_workers=DEFAULT_MAX_WORKERS, on_progress=None):
    records = fetch_factory_order_records(
        ACCEPTED,
        time_range=get_past_unfinished_time_range(days_before=days_before)
    )
    record_by_order_id = {
        record.get("no"): record
        for record in records
        if record.get("no")
    }
    order_ids = list(record_by_order_id.keys())
    return fetch_unproduced_orders_with_tracking(
        max_workers=max_workers,
        on_progress=on_progress,
        order_ids=order_ids,
        record_by_order_id=record_by_order_id
    )


def format_tracking_preview_row(scan_result, record=None):
    record = record or {}
    tracking_number = scan_result.get("tracking", "")
    return {
        "Order ID": scan_result.get("Order ID", ""),
        "Merchant Order No": record.get("merchantOrderNo", ""),
        "Same Order Count": record.get("sameOrderValidNum", ""),
        "Item Quantity": record.get("num", ""),
        "Tracking Number": tracking_number,
        "Carrier": scan_result.get("carrier", ""),
        "Status": "已找到" if tracking_number else scan_result.get("msg", "")
    }
