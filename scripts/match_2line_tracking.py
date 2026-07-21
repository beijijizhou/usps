import csv
import json
import sys
import time
import tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from pathlib import Path

import requests


TRACKING_TEXT = """
label_id
9202090383922309753053
9202090383922309679452
9202090383922309754296
9202090383922309672040
9202090383922309674846
9202090383922309652950
9202090383922309569944
9200190420634900001073
9200190420634900001141
9202090383922309564802
9202090383922309513053
9202090383922309561931
9202090569324261734312
9202090383922309454295
9202090383922309376771
9202090383922309372070
9202091687351775620673
9202090383922309211393
9202090383922309213182
9202090383922309214394
9200190420145900004280
9200190420183800053434
9202090383922309189647
9202090383922309186561
9200190390471823240659
9200190419998800052981
9202090383922309107238
9202090383922309106750
9202090383922309105791
9202090383922309106590
9202090383922309107856
9202090383922308854966
9202090383922308853273
9202090383922308856168
9202090383922308760007
9261290349244052749316
9200190419393800003764
9200190419393800003733
9202090383922308689308
9202090383922308686307
9202090383922308630768
9202090383922308631482
9202090383922308630843
9202090383922308531553
9202090383922308532536
9300110990513323924057
9300111038700134705203
9261290349243383636890
"""

PLATFORM = "2号线"
START_DATE = date(2026, 5, 1)
END_DATE = date.today()
STATUS = 6
PAGE_SIZE = 10000
MAX_WORKERS = 300
OUTPUT_PATH = Path("output/2号线_tracking_match_2026-05-01.csv")

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
FACTORY_LOGIN_URL = "https://factory-api.sdspod.com/login"
QA_LOGIN_URL = "https://g-pod-api.sdspod.com/pod/auth/login"
FACTORY_ORDERS_URL = "https://factory-api.sdspod.com/factory_orders/v2/order/allByEs"
PARCEL_DETAIL_URL = "https://pod-api.sdspod.com/pod/parcel/qc/{order_id}/detail"


def parse_tracking_numbers(raw_text):
    tracking_numbers = []
    seen = set()
    for line in raw_text.replace(",", "\n").replace("\t", "\n").splitlines():
        tracking_number = line.strip()
        if not tracking_number or tracking_number.lower() in {"label_id", "tracking", "tracking number"}:
            continue
        if tracking_number in seen:
            continue
        seen.add(tracking_number)
        tracking_numbers.append(tracking_number)
    return tracking_numbers


def load_secrets():
    with open(".streamlit/secrets.toml", "rb") as file:
        return tomllib.load(file)


def login_factory(secrets):
    creds = secrets["factory_credentials"][PLATFORM]
    payload = {
        "contact_tel": creds["contact_tel"],
        "extraInfo": creds["extraInfo"],
        "factory_code": creds["factory_code"],
        "password": creds["password"],
    }
    response = requests.post(FACTORY_LOGIN_URL, json=payload, headers=login_headers(), timeout=30)
    data = response.json()
    token = data.get("data", {}).get("access_token") or data.get("data", {}).get("token")
    if not token:
        raise RuntimeError(f"Factory login failed: HTTP {response.status_code}")
    return token


def login_qa(secrets):
    creds = secrets["qa_credentials"][PLATFORM]
    payload = {
        "extraInfo": creds["extraInfo"],
        "no": creds["no"],
        "password": creds["password"],
        "username": creds["username"],
    }
    params = {"t": int(time.time() * 1000)}
    response = requests.post(QA_LOGIN_URL, json=payload, params=params, headers=login_headers(), timeout=30)
    data = response.json()
    token = data.get("token") or data.get("data", {}).get("token") or data.get("data", {}).get("accessToken")
    if not token:
        raise RuntimeError(f"QA login failed: HTTP {response.status_code}")
    return token


def login_headers():
    return {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": USER_AGENT,
    }


def token_headers(token):
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "access-token": token,
    }


def date_range():
    start_dt = datetime.combine(START_DATE, datetime.min.time())
    end_dt = datetime.combine(END_DATE, datetime.max.time()).replace(microsecond=0)
    return {
        "startTime": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "endTime": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
    }


def fetch_factory_records(factory_token):
    headers = token_headers(factory_token)
    records = []
    for page in range(1, 200):
        params = {
            "size": PAGE_SIZE,
            "page": page,
            "status": STATUS,
            "noManuscriptFeedbackStatus": 1,
            "sort": "-id",
            **date_range(),
        }
        response = requests.get(FACTORY_ORDERS_URL, params=params, headers=headers, timeout=60)
        if response.status_code != 200:
            raise RuntimeError(f"Factory records failed: HTTP {response.status_code} {response.text[:300]}")
        page_records = response.json().get("records", [])
        records.extend(page_records)
        print(f"已拉取历史订单 page={page}, 本页={len(page_records)}, 累计={len(records)}", flush=True)
        if len(page_records) < PAGE_SIZE:
            break
    return records


def extract_order_id(record):
    order = record.get("order") or {}
    return str(order.get("id") or record.get("orderId") or "").strip()


def query_parcel_detail(record, qa_headers):
    order_id = extract_order_id(record)
    if not order_id:
        return []
    try:
        response = requests.get(
            PARCEL_DETAIL_URL.format(order_id=order_id),
            params={"t": int(time.time() * 1000)},
            headers=qa_headers,
            timeout=(5, 30),
        )
        if response.status_code != 200:
            return []
        rows = []
        detail_list = response.json().get("detailList", [])
        for parcel in detail_list:
            tracking_number = str(parcel.get("carriageNo", "")).strip()
            if not tracking_number:
                continue
            rows.append({
                "Order ID": record.get("no", ""),
                "Merchant Order No": record.get("merchantOrderNo", ""),
                "Tracking Number": tracking_number,
                "Carrier": parcel.get("carriageName", ""),
                "Factory Status": record.get("status", ""),
                "Begin Time": record.get("beginTime", ""),
                "Finished Time": record.get("finishedTime", ""),
                "Ship Time": record.get("shipTime", ""),
                "PDF": parcel.get("pdfUrl") or parcel.get("laberPdf", ""),
                "Match Status": "已找到",
            })
        return rows
    except Exception:
        return []


def write_csv(rows):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Input Tracking Number",
        "Match Status",
        "Order ID",
        "Merchant Order No",
        "Tracking Number",
        "Carrier",
        "Factory Status",
        "Begin Time",
        "Finished Time",
        "Ship Time",
        "PDF",
    ]
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    targets = parse_tracking_numbers(TRACKING_TEXT)
    target_set = set(targets)
    print(f"输入 tracking 数量: {len(targets)}", flush=True)

    secrets = load_secrets()
    factory_token = login_factory(secrets)
    qa_token = login_qa(secrets)
    print("登录成功，开始拉取 2号线历史订单。", flush=True)

    records = fetch_factory_records(factory_token)
    qa_headers = token_headers(qa_token)
    found_by_tracking = {}
    total = len(records)
    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_record = {
            executor.submit(query_parcel_detail, record, qa_headers): record
            for record in records
            if extract_order_id(record)
        }
        for future in as_completed(future_to_record):
            completed += 1
            for row in future.result():
                tracking_number = row["Tracking Number"]
                if tracking_number in target_set and tracking_number not in found_by_tracking:
                    found_by_tracking[tracking_number] = row
                    print(f"找到 {len(found_by_tracking)}/{len(targets)}: {tracking_number} -> {row['Order ID']}", flush=True)
            if completed % 1000 == 0 or len(found_by_tracking) == len(targets):
                print(f"已查询包裹详情 {completed}/{total}, 已找到 {len(found_by_tracking)}/{len(targets)}", flush=True)
            if len(found_by_tracking) == len(targets):
                break

    output_rows = []
    for tracking_number in targets:
        found = found_by_tracking.get(tracking_number)
        if found:
            output_rows.append({"Input Tracking Number": tracking_number, **found})
        else:
            output_rows.append({
                "Input Tracking Number": tracking_number,
                "Match Status": "未找到",
                "Order ID": "",
                "Merchant Order No": "",
                "Tracking Number": tracking_number,
                "Carrier": "",
                "Factory Status": "",
                "Begin Time": "",
                "Finished Time": "",
                "Ship Time": "",
                "PDF": "",
            })

    write_csv(output_rows)
    print(json.dumps({
        "input_count": len(targets),
        "found_count": len(found_by_tracking),
        "missing_count": len(targets) - len(found_by_tracking),
        "output_path": str(OUTPUT_PATH.resolve()),
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
