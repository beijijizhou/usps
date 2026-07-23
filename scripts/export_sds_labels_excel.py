import json
import sys
import time
import tomllib
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from pathlib import Path
from xml.sax.saxutils import escape

import requests


PLATFORMS = ["1号线", "2号线", "忆点万象", "3D热转印"]
START_DATE = date(2026, 5, 1)
END_DATE = date(2026, 7, 31)
STATUS = 6
PAGE_SIZE = 10000
MAX_WORKERS = 12
QUERY_BATCH_SIZE = 200
PROGRESS_EVERY = 20
OUTPUT_PATH = Path("output/sds_labels_2026-05_to_2026-07.xlsx")
USPS_ONLY = False

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
FACTORY_LOGIN_URL = "https://factory-api.sdspod.com/login"
QA_LOGIN_URL = "https://g-pod-api.sdspod.com/pod/auth/login"
FACTORY_ORDERS_URL = "https://factory-api.sdspod.com/factory_orders/v2/order/allByEs"
PARCEL_DETAIL_URL = "https://pod-api.sdspod.com/pod/parcel/qc/{order_id}/detail"

LABEL_COLUMNS = [
    "平台",
    "SDS订单号",
    "销售订单号",
    "系统订单ID",
    "物流单号",
    "物流渠道",
    "服务商",
    "物流ID",
    "物流代码ID",
    "包裹ID",
    "包裹名称",
    "包裹状态",
    "工厂状态",
    "开始时间",
    "完成时间",
    "发货时间",
    "面单PDF",
    "面单PDF备用",
    "面单状态",
]
ERROR_COLUMNS = ["平台", "阶段", "错误"]


def load_secrets():
    with open(".streamlit/secrets.toml", "rb") as file:
        return tomllib.load(file)


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


def login_factory(secrets, platform):
    creds = secrets["factory_credentials"][platform]
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
        raise RuntimeError(f"Factory login failed: HTTP {response.status_code} {safe_message(data)}")
    return token


def login_qa(secrets, platform):
    creds = secrets["qa_credentials"][platform]
    payload = {
        "extraInfo": creds["extraInfo"],
        "no": creds["no"],
        "password": creds["password"],
        "username": creds["username"],
    }
    response = requests.post(
        QA_LOGIN_URL,
        json=payload,
        params={"t": int(time.time() * 1000)},
        headers=login_headers(),
        timeout=30,
    )
    data = response.json()
    token = data.get("token") or data.get("data", {}).get("token") or data.get("data", {}).get("accessToken")
    if not token:
        raise RuntimeError(f"QA login failed: HTTP {response.status_code} {safe_message(data)}")
    return token


def safe_message(data):
    text = json.dumps(data, ensure_ascii=False)
    for key in ["token", "access_token", "accessToken"]:
        text = text.replace(key, "[redacted-key]")
    return text[:300]


def date_range():
    start_dt = datetime.combine(START_DATE, datetime.min.time())
    end_dt = datetime.combine(END_DATE, datetime.max.time()).replace(microsecond=0)
    return {
        "startTime": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "endTime": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
    }


def fetch_factory_records(platform, factory_token):
    headers = token_headers(factory_token)
    records = []
    start_dt = datetime.combine(START_DATE, datetime.min.time())
    end_dt = datetime.combine(END_DATE, datetime.max.time()).replace(microsecond=0)

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
        filtered_records = [
            record for record in page_records
            if is_record_in_date_range(record, start_dt, end_dt)
        ]
        records.extend(filtered_records)
        print(
            f"{platform}: 已拉取历史订单 page={page}, 本页={len(page_records)}, 本月保留={len(filtered_records)}, 累计={len(records)}",
            flush=True
        )

        if len(page_records) < PAGE_SIZE:
            break
        if should_stop_paging(page_records, start_dt):
            print(f"{platform}: 本页已早于开始日期，停止继续翻页。", flush=True)
            break

    return records


def parse_record_datetime(record):
    for key in ["beginTime", "gmtCreateTime", "createTime"]:
        value = record.get(key)
        if not value:
            continue
        try:
            return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return None


def is_record_in_date_range(record, start_dt, end_dt):
    record_dt = parse_record_datetime(record)
    return bool(record_dt and start_dt <= record_dt <= end_dt)


def should_stop_paging(page_records, start_dt):
    record_dates = [
        parse_record_datetime(record)
        for record in page_records
    ]
    record_dates = [record_dt for record_dt in record_dates if record_dt]
    return bool(record_dates and max(record_dates) < start_dt)


def extract_order_id(record):
    order = record.get("order") or {}
    return str(order.get("id") or record.get("orderId") or "").strip()


def query_parcel_rows(platform, record, qa_headers):
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
        for parcel in response.json().get("detailList", []):
            tracking_number = str(parcel.get("carriageNo", "")).strip()
            if not tracking_number:
                continue
            if USPS_ONLY and not is_usps_parcel(parcel):
                continue

            rows.append({
                "平台": platform,
                "SDS订单号": record.get("no", ""),
                "销售订单号": record.get("merchantOrderNo", ""),
                "系统订单ID": order_id,
                "物流单号": tracking_number,
                "物流渠道": parcel.get("carriageName", ""),
                "服务商": parcel.get("serviceProviderName", ""),
                "物流ID": parcel.get("logisticsId", ""),
                "物流代码ID": parcel.get("logisticsCodeId", ""),
                "包裹ID": parcel.get("parcelId", ""),
                "包裹名称": parcel.get("parcelName", ""),
                "包裹状态": parcel.get("status", ""),
                "工厂状态": record.get("status", ""),
                "开始时间": record.get("beginTime", ""),
                "完成时间": record.get("finishedTime", ""),
                "发货时间": record.get("shipTime", ""),
                "面单PDF": parcel.get("pdfUrl", ""),
                "面单PDF备用": parcel.get("laberPdf", ""),
                "面单状态": parcel.get("scanFormStatus", ""),
            })
        return rows
    except Exception:
        return []


def is_usps_parcel(parcel):
    tracking_number = str(parcel.get("carriageNo", "")).strip()
    carrier_name = str(parcel.get("carriageName", "")).upper()
    service_provider_name = str(parcel.get("serviceProviderName", "")).upper()
    logistics_code = str(parcel.get("logisticsCodeId", "")).upper()

    return (
        tracking_number.startswith("9")
        or "USPS" in carrier_name
        or "USPS" in service_provider_name
        or "USPS" in logistics_code
    )


def export_platform(secrets, platform):
    errors = []
    try:
        factory_token = login_factory(secrets, platform)
        qa_token = login_qa(secrets, platform)
    except Exception as exc:
        return [], [{"平台": platform, "阶段": "登录", "错误": str(exc)}]

    try:
        records = fetch_factory_records(platform, factory_token)
    except Exception as exc:
        return [], [{"平台": platform, "阶段": "拉取历史订单", "错误": str(exc)}]

    rows = []
    qa_headers = token_headers(qa_token)
    records_with_order_id = [record for record in records if extract_order_id(record)]
    total = len(records_with_order_id)

    completed = 0
    for start_index in range(0, total, QUERY_BATCH_SIZE):
        batch_records = records_with_order_id[start_index:start_index + QUERY_BATCH_SIZE]
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(batch_records)) if batch_records else 1) as executor:
            futures = {
                executor.submit(query_parcel_rows, platform, record, qa_headers): record
                for record in batch_records
            }
            for future in as_completed(futures):
                completed += 1
                rows.extend(future.result())
                if completed % PROGRESS_EVERY == 0 or completed == total:
                    print(f"{platform}: 已查询包裹详情 {completed}/{total}, 已导出面单 {len(rows)}", flush=True)

    return rows, errors


def write_xlsx(path, sheets):
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet_names = list(sheets.keys())
    shared_strings = []
    shared_string_index = {}
    sheet_xml = {}

    for sheet_name, rows in sheets.items():
        normalized_rows = [[str(cell or "") for cell in row] for row in rows]
        sheet_xml[sheet_name] = build_sheet_xml(normalized_rows, shared_strings, shared_string_index)

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr("[Content_Types].xml", build_content_types(len(sheet_names)))
        workbook.writestr("_rels/.rels", build_root_rels())
        workbook.writestr("xl/workbook.xml", build_workbook_xml(sheet_names))
        workbook.writestr("xl/_rels/workbook.xml.rels", build_workbook_rels(sheet_names))
        workbook.writestr("xl/sharedStrings.xml", build_shared_strings_xml(shared_strings))
        workbook.writestr("xl/styles.xml", build_styles_xml())
        for index, sheet_name in enumerate(sheet_names, start=1):
            workbook.writestr(f"xl/worksheets/sheet{index}.xml", sheet_xml[sheet_name])


def build_sheet_rows(headers, dict_rows):
    return [headers] + [[row.get(header, "") for header in headers] for row in dict_rows]


def build_sheet_xml(rows, shared_strings, shared_string_index):
    xml_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            cell_ref = f"{column_name(col_index)}{row_index}"
            if value not in shared_string_index:
                shared_string_index[value] = len(shared_strings)
                shared_strings.append(value)
            cells.append(f'<c r="{cell_ref}" t="s"><v>{shared_string_index[value]}</v></c>')
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/>'
        f'<sheetData>{"".join(xml_rows)}</sheetData>'
        '</worksheet>'
    )


def column_name(index):
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def build_shared_strings_xml(strings):
    items = "".join(f"<si><t>{escape(text)}</t></si>" for text in strings)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">'
        f"{items}</sst>"
    )


def build_content_types(sheet_count):
    sheet_overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for index in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        f"{sheet_overrides}</Types>"
    )


def build_root_rels():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )


def build_workbook_xml(sheet_names):
    sheets = "".join(
        f'<sheet name="{escape(sheet_name)}" sheetId="{index}" r:id="rId{index}"/>'
        for index, sheet_name in enumerate(sheet_names, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{sheets}</sheets></workbook>"
    )


def build_workbook_rels(sheet_names):
    rels = "".join(
        f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        for index in range(1, len(sheet_names) + 1)
    )
    shared_id = len(sheet_names) + 1
    styles_id = len(sheet_names) + 2
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{rels}"
        f'<Relationship Id="rId{shared_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
        f'<Relationship Id="rId{styles_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    )


def build_styles_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
        '</styleSheet>'
    )


def main():
    secrets = load_secrets()
    all_rows = []
    all_errors = []

    for platform in PLATFORMS:
        print(f"开始导出 {platform}", flush=True)
        rows, errors = export_platform(secrets, platform)
        all_rows.extend(rows)
        all_errors.extend(errors)
        print(f"{platform}: 完成，面单记录 {len(rows)}，错误 {len(errors)}", flush=True)

    sheets = {
        "面单数据": build_sheet_rows(LABEL_COLUMNS, all_rows),
        "错误记录": build_sheet_rows(ERROR_COLUMNS, all_errors),
    }
    write_xlsx(OUTPUT_PATH, sheets)
    print(json.dumps({
        "output_path": str(OUTPUT_PATH.resolve()),
        "label_rows": len(all_rows),
        "errors": all_errors,
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
