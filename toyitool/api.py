import math
from datetime import date, datetime, time

import requests


BASE_URL = "https://gc.toyitool.com/prod-api/factory/gc/orderInfo/list"
OUTBOUND_URL = "https://gc.toyitool.com/prod-api/factory/gc/orderInfo/outbound"
CLIENT_ID = "633fa59f083ed7b06a79c27cd1f11411"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)
ORDER_STATUS_VALUES = {
    "PRODUCTION": "2",
    "PICKING": "1",
    "SHIPPED": "3",
}

ORDER_ID_KEYS = [
    "id",
    "orderId",
    "order_id",
    "orderInfoId",
    "gcOrderInfoId",
]
ORDER_NUMBER_KEYS = [
    "orderNo",
    "order_no",
    "orderNum",
    "orderNumber",
    "order_number",
    "orderCode",
    "order_code",
    "platformOrderNo",
    "platform_order_no",
    "sourceOrderNo",
    "source_order_no",
    "thirdOrderNo",
    "third_order_no",
    "merchantOrderNo",
    "merchant_order_no",
    "saleOrderNo",
    "salesOrderNo",
    "webOrderItemId",
    "outOrderId",
]


def normalize_authorization(value):
    token = str(value or "").strip()
    if not token:
        return ""
    if token.lower().startswith("bearer "):
        return token
    return f"Bearer {token}"


def build_headers(authorization, referer="https://gc.toyitool.com/orderManagement/myOrder", content_type=None):
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Authorization": normalize_authorization(authorization),
        "Connection": "keep-alive",
        "Content-Language": "zh_CN",
        "Referer": referer,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": DEFAULT_USER_AGENT,
        "clientid": CLIENT_ID,
    }
    if content_type:
        headers["Content-Type"] = content_type
        headers["Origin"] = "https://gc.toyitool.com"
    return headers


def build_list_headers(authorization):
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Authorization": normalize_authorization(authorization),
        "Connection": "keep-alive",
        "Content-Language": "zh_CN",
        "Referer": "https://gc.toyitool.com/orderManagement/myOrder",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": DEFAULT_USER_AGENT,
        "clientid": CLIENT_ID,
    }


def datetime_string(day, end_of_day=False):
    clock = time.max.replace(microsecond=0) if end_of_day else time.min
    return datetime.combine(day, clock).strftime("%Y-%m-%d %H:%M:%S")


def build_params(page_num, page_size, time_type, start_date=None, end_date=None, order_status=None):
    params = {
        "timeType": time_type,
        "pageNum": page_num,
        "pageSize": page_size,
    }
    if order_status and order_status != "全部":
        params["orderStatus"] = ORDER_STATUS_VALUES.get(str(order_status).upper(), order_status)
    if start_date:
        params["beginTime"] = datetime_string(start_date)
    if end_date:
        params["endTime"] = datetime_string(end_date, end_of_day=True)
    return params


def extract_rows(data):
    if not isinstance(data, dict):
        return []
    for key in ["rows", "records", "list", "data"]:
        value = data.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested_rows = extract_rows(value)
            if nested_rows:
                return nested_rows
    return []


def extract_total(data, fallback_count=0):
    if not isinstance(data, dict):
        return fallback_count
    for key in ["total", "totalCount", "count"]:
        value = data.get(key)
        if value not in [None, ""]:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
    nested_data = data.get("data")
    if isinstance(nested_data, dict):
        return extract_total(nested_data, fallback_count=fallback_count)
    return fallback_count


def first_present(row, keys):
    for key in keys:
        value = row.get(key)
        if value not in [None, ""] and not isinstance(value, bool):
            return value
    return ""


def flatten_value(value):
    if isinstance(value, (str, int, float)) or value is None:
        return "" if value is None else value
    return str(value)


def normalize_order_row(row):
    mid_items = row.get("midSubList") if isinstance(row.get("midSubList"), list) else []
    web_order_items = row.get("webOrderList") if isinstance(row.get("webOrderList"), list) else []
    first_mid_item = mid_items[0] if mid_items and isinstance(mid_items[0], dict) else {}
    first_web_order = web_order_items[0] if web_order_items and isinstance(web_order_items[0], dict) else {}

    normalized = {
        "订单ID": first_present(row, ORDER_ID_KEYS),
        "订单号": (
            first_present(row, ORDER_NUMBER_KEYS)
            or first_present(first_mid_item, ORDER_NUMBER_KEYS)
            or first_present(first_web_order, ORDER_NUMBER_KEYS)
        ),
        "生产项ID": first_present(first_mid_item, ["orderItemId"]),
        "物流单号": first_present(first_mid_item, ["shippingNo"]),
        "物流渠道": first_present(first_mid_item, ["shippingName"]),
        "面单PDF": first_present(first_mid_item, ["shippingUrl"]),
        "商品SKU": first_present(first_mid_item, ["skuCode"]),
        "商品名称": first_present(first_mid_item, ["productName", "skuTitle"]),
        "生产批次": first_present(first_mid_item, ["planCode"]),
    }

    passthrough_keys = [
        "status",
        "orderStatus",
        "assignTime",
        "assign_time",
        "createTime",
        "create_time",
        "deliveryNo",
        "trackingNo",
        "logisticsNo",
    ]
    for key in passthrough_keys:
        value = row.get(key)
        if value not in [None, ""]:
            normalized[key] = flatten_value(value)

    if not normalized["订单号"]:
        for key, value in row.items():
            lowered_key = str(key).lower()
            if "order" in lowered_key and "no" in lowered_key and value not in [None, ""] and not isinstance(value, bool):
                normalized["订单号"] = flatten_value(value)
                break

    return normalized


def fetch_order_page(authorization, page_num=1, page_size=10, time_type="s.assign_time", start_date=None, end_date=None, order_status=None):
    if not normalize_authorization(authorization):
        raise ValueError("Authorization 为空")

    response = requests.get(
        BASE_URL,
        headers=build_headers(authorization),
        params=build_params(page_num, page_size, time_type, start_date, end_date, order_status),
        timeout=30,
    )
    try:
        data = response.json()
    except ValueError:
        data = {"msg": response.text}

    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}: {str(data)[:300]}")

    code = data.get("code") if isinstance(data, dict) else None
    if code not in [None, 0, 200, "0", "200"]:
        message = data.get("msg") or data.get("message") or data
        raise RuntimeError(f"接口返回失败：{message}")

    rows = extract_rows(data)
    total = extract_total(data, fallback_count=len(rows))
    return {
        "rows": rows,
        "normalized_rows": [normalize_order_row(row) for row in rows if isinstance(row, dict)],
        "total": total,
        "page_num": page_num,
        "page_size": page_size,
        "raw": data,
    }


def fetch_order_pages(authorization, page_size=100, max_pages=1, time_type="s.assign_time", start_date=None, end_date=None, order_status=None, on_progress=None):
    first_page = fetch_order_page(
        authorization=authorization,
        page_num=1,
        page_size=page_size,
        time_type=time_type,
        start_date=start_date,
        end_date=end_date,
        order_status=order_status,
    )
    all_rows = list(first_page["normalized_rows"])
    total = first_page["total"]
    total_pages = max(1, math.ceil(total / page_size)) if total else 1
    pages_to_fetch = min(max_pages, total_pages)
    if on_progress:
        on_progress(1, pages_to_fetch, len(all_rows), total)

    for page_num in range(2, pages_to_fetch + 1):
        page = fetch_order_page(
            authorization=authorization,
            page_num=page_num,
            page_size=page_size,
            time_type=time_type,
            start_date=start_date,
            end_date=end_date,
            order_status=order_status,
        )
        all_rows.extend(page["normalized_rows"])
        if on_progress:
            on_progress(page_num, pages_to_fetch, len(all_rows), total)

    return {
        "rows": all_rows,
        "total": total,
        "fetched": len(all_rows),
        "pages_fetched": pages_to_fetch,
    }


def filter_by_order_status(rows, order_status):
    if not order_status or order_status == "全部":
        return rows
    return [
        row for row in rows
        if str(row.get("orderStatus", "")).strip().upper() == str(order_status).strip().upper()
    ]


def is_success_response(data):
    if not isinstance(data, dict):
        return False
    code = data.get("code")
    success = data.get("success")
    if success is True:
        return True
    return code in [0, 200, "0", "200"]


def extract_message(data):
    if not isinstance(data, dict):
        return str(data or "")
    return str(data.get("msg") or data.get("message") or data)


def outbound_orders(authorization, order_ids):
    clean_order_ids = [
        str(order_id).strip()
        for order_id in order_ids
        if str(order_id or "").strip()
    ]
    if not clean_order_ids:
        raise ValueError("没有可出库/出面单的订单ID")

    response = requests.post(
        OUTBOUND_URL,
        headers=build_headers(
            authorization,
            referer="https://gc.toyitool.com/orderOutbound",
            content_type="application/json;charset=UTF-8",
        ),
        json={"orderIds": clean_order_ids},
        timeout=60,
    )
    try:
        data = response.json()
    except ValueError:
        data = {"msg": response.text}

    return {
        "ok": response.status_code == 200 and is_success_response(data),
        "http_status": response.status_code,
        "message": extract_message(data),
        "order_count": len(clean_order_ids),
        "order_ids": clean_order_ids,
        "raw": data,
    }
