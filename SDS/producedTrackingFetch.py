import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests

from SDS.headers import get_qa_headers
from SDS.factoryFetch import COMPLETED, fetch_factory_order_records
from SDS.pre_scan import DEFAULT_MAX_WORKERS, run_parallel_scan_generator

PARCEL_DETAIL_TIMEOUT = (5, 30)
PARCEL_DETAIL_URL = "https://pod-api.sdspod.com/pod/parcel/qc/{order_id}/detail"


def parse_tracking_numbers(raw_text):
    tracking_numbers = []
    seen = set()

    for line in str(raw_text or "").replace(",", "\n").replace("\t", "\n").splitlines():
        tracking_number = line.strip()
        if not tracking_number or tracking_number.lower() in {"label_id", "tracking", "tracking number"}:
            continue
        if tracking_number in seen:
            continue

        seen.add(tracking_number)
        tracking_numbers.append(tracking_number)

    return tracking_numbers


def build_time_range_from_dates(start_date, end_date):
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time()).replace(microsecond=0)

    return {
        "startTime": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "endTime": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
    }


def fetch_produced_order_records_since(start_date, end_date, statuses=None):
    statuses = statuses or [COMPLETED]
    time_range = build_time_range_from_dates(start_date, end_date)
    records = []
    seen_order_ids = set()

    for status in statuses:
        for record in fetch_factory_order_records(status, time_range=time_range):
            order_id = str(record.get("no", "")).strip()
            if not order_id or order_id in seen_order_ids:
                continue

            seen_order_ids.add(order_id)
            records.append(record)

    return records


def fetch_produced_tracking_since(start_date, end_date, statuses=None, max_workers=DEFAULT_MAX_WORKERS, on_progress=None):
    records = fetch_produced_order_records_since(start_date, end_date, statuses=statuses)
    order_ids = [str(record.get("no", "")).strip() for record in records if str(record.get("no", "")).strip()]
    record_by_order_id = {str(record.get("no", "")).strip(): record for record in records}
    rows = []
    total = len(order_ids)

    for index, result in enumerate(run_parallel_scan_generator(order_ids, max_workers=max_workers), start=1):
        order_id = str(result.get("Order ID", "")).strip()
        factory_record = record_by_order_id.get(order_id, {})
        rows.append(format_produced_tracking_row(result, factory_record))

        if on_progress:
            on_progress(index, total, result)

    return order_ids, rows


def find_tracking_numbers_in_produced_history(
    raw_tracking_numbers,
    start_date,
    end_date,
    statuses=None,
    max_workers=DEFAULT_MAX_WORKERS,
    on_progress=None,
    chunk_size=1000,
):
    target_tracking_numbers = parse_tracking_numbers(raw_tracking_numbers)
    target_set = set(target_tracking_numbers)
    if not target_tracking_numbers:
        return [], [], []

    records = fetch_produced_order_records_since(start_date, end_date, statuses=statuses)
    order_ids = [str(record.get("no", "")).strip() for record in records if str(record.get("no", "")).strip()]
    record_by_order_id = {str(record.get("no", "")).strip(): record for record in records}
    found_rows = []
    found_tracking_numbers = set()
    queried = 0
    total = len(order_ids)

    for start_index in range(0, total, chunk_size):
        if found_tracking_numbers >= target_set:
            break

        chunk_order_ids = order_ids[start_index:start_index + chunk_size]
        for result in run_parallel_scan_generator(chunk_order_ids, max_workers=max_workers):
            queried += 1
            order_id = str(result.get("Order ID", "")).strip()
            tracking_number = str(result.get("tracking", "")).strip()

            if tracking_number in target_set and tracking_number not in found_tracking_numbers:
                factory_record = record_by_order_id.get(order_id, {})
                found_rows.append({
                    **format_produced_tracking_row(result, factory_record),
                    "Match Status": "已找到",
                })
                found_tracking_numbers.add(tracking_number)

            if on_progress:
                on_progress(queried, total, result)

        if found_tracking_numbers >= target_set:
            break

    found_tracking_numbers = {
        str(row.get("Tracking Number", "")).strip()
        for row in found_rows
        if str(row.get("Tracking Number", "")).strip()
    }
    missing_rows = [
        {
            "Order ID": "",
            "Merchant Order No": "",
            "Tracking Number": tracking_number,
            "Carrier": "",
            "Factory Status": "",
            "Begin Time": "",
            "Finished Time": "",
            "Ship Time": "",
            "Status": "2号线历史数据中未找到",
            "Match Status": "未找到",
        }
        for tracking_number in target_tracking_numbers
        if tracking_number not in found_tracking_numbers
    ]

    return target_tracking_numbers, found_rows, missing_rows


def find_tracking_numbers_in_platform_history(
    raw_tracking_numbers,
    start_date,
    end_date,
    platform_name,
    statuses=None,
    max_workers=DEFAULT_MAX_WORKERS,
    on_progress=None,
):
    target_tracking_numbers = parse_tracking_numbers(raw_tracking_numbers)
    target_set = set(target_tracking_numbers)
    if not target_tracking_numbers:
        return [], [], []

    records = fetch_produced_order_records_since(start_date, end_date, statuses=statuses)
    qa_headers = get_qa_headers()
    found_rows = []
    found_tracking_numbers = set()
    total = len(records)
    queried = 0
    worker_count = min(max_workers, total) if total else 0

    if not worker_count:
        return build_platform_lookup_result(target_tracking_numbers, found_rows, platform_name)

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(query_record_parcel_rows, record, qa_headers, platform_name): record
            for record in records
            if extract_order_id(record)
        }
        for future in as_completed(futures):
            queried += 1
            rows = future.result()
            latest_result = {"Order ID": futures[future].get("no", "")}

            for row in rows:
                tracking_number = str(row.get("Tracking Number", "")).strip()
                latest_result = {"Order ID": row.get("Order ID", "")}
                if tracking_number in target_set and tracking_number not in found_tracking_numbers:
                    found_rows.append({**row, "Match Status": "已找到"})
                    found_tracking_numbers.add(tracking_number)

            if on_progress:
                on_progress(queried, total, latest_result, platform_name, len(found_tracking_numbers), len(target_set))

            if found_tracking_numbers >= target_set:
                break

    return build_platform_lookup_result(target_tracking_numbers, found_rows, platform_name)


def build_platform_lookup_result(target_tracking_numbers, found_rows, platform_name):
    found_tracking_numbers = {
        str(row.get("Tracking Number", "")).strip()
        for row in found_rows
        if str(row.get("Tracking Number", "")).strip()
    }
    missing_rows = [
        {
            "Platform": platform_name,
            "Order ID": "",
            "Merchant Order No": "",
            "Tracking Number": tracking_number,
            "Carrier": "",
            "Factory Status": "",
            "Begin Time": "",
            "Finished Time": "",
            "Ship Time": "",
            "PDF": "",
            "Status": f"{platform_name} 历史数据中未找到",
            "Match Status": "未找到",
        }
        for tracking_number in target_tracking_numbers
        if tracking_number not in found_tracking_numbers
    ]
    return target_tracking_numbers, found_rows, missing_rows


def extract_order_id(record):
    order = record.get("order") or {}
    return str(order.get("id") or record.get("orderId") or "").strip()


def query_record_parcel_rows(record, headers, platform_name):
    order_id = extract_order_id(record)
    if not order_id:
        return []

    try:
        response = requests.get(
            PARCEL_DETAIL_URL.format(order_id=order_id),
            params={"t": int(time.time() * 1000)},
            headers=headers,
            timeout=PARCEL_DETAIL_TIMEOUT,
        )
        if response.status_code != 200:
            return []

        rows = []
        for parcel in response.json().get("detailList", []):
            tracking_number = str(parcel.get("carriageNo", "")).strip()
            if not tracking_number:
                continue

            rows.append({
                "Platform": platform_name,
                "Order ID": record.get("no", ""),
                "Merchant Order No": record.get("merchantOrderNo", ""),
                "Tracking Number": tracking_number,
                "Carrier": parcel.get("carriageName", ""),
                "Factory Status": record.get("status", ""),
                "Begin Time": record.get("beginTime", ""),
                "Finished Time": record.get("finishedTime", ""),
                "Ship Time": record.get("shipTime", ""),
                "PDF": parcel.get("pdfUrl") or parcel.get("laberPdf", ""),
                "Status": "已找到",
            })
        return rows
    except Exception:
        return []


def format_produced_tracking_row(scan_result, factory_record):
    tracking_number = scan_result.get("tracking", "")
    return {
        "Order ID": scan_result.get("Order ID", ""),
        "Merchant Order No": factory_record.get("merchantOrderNo", ""),
        "Tracking Number": tracking_number,
        "Carrier": scan_result.get("carrier", ""),
        "Factory Status": factory_record.get("status", ""),
        "Begin Time": factory_record.get("beginTime", ""),
        "Finished Time": factory_record.get("finishedTime", ""),
        "Ship Time": factory_record.get("shipTime", ""),
        "Status": "已找到" if tracking_number else scan_result.get("msg", ""),
    }
