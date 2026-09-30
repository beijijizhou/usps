"""S2B 生产批次读取：列出最近批次、读取批次内的订单号。

接口与 automatic-print 相同（overseasfactory.s2bdiy.com），直接用工厂 token 调用。
"""
import requests

API_ROOT = "https://overseasfactory.s2bdiy.com/req"
DEFAULT_TIMEOUT = 30


class S2BBatchError(RuntimeError):
    pass


def _post(token, path, payload, timeout=DEFAULT_TIMEOUT):
    if not token:
        raise S2BBatchError("token 为空，请检查 Streamlit secrets 的 s2b_tokens 配置")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"Bearer {token}",
        "Origin": "https://overseasfactory.s2bdiy.com",
        "Referer": "https://overseasfactory.s2bdiy.com/factory/orderManage",
    }
    try:
        response = requests.post(API_ROOT + path, json=payload, headers=headers, timeout=timeout)
    except requests.RequestException as error:
        raise S2BBatchError(f"无法连接 S2B：{error}") from error

    if response.status_code in (401, 403):
        raise S2BBatchError(f"S2B 登录已失效或没有权限（HTTP {response.status_code}）")
    try:
        body = response.json()
    except ValueError as error:
        raise S2BBatchError(f"S2B 返回 HTTP {response.status_code}：{response.text[:200]}") from error

    ok = response.ok and (
        str(body.get("status_code")) == "200" or body.get("status") == "success"
    )
    if not ok:
        raise S2BBatchError(str(body.get("msg") or body.get("message") or f"S2B 返回 HTTP {response.status_code}"))

    data = body.get("data")
    return data if isinstance(data, dict) else {}


def list_batches(token, limit=50):
    """返回最近 limit 个批次（S2B 默认按创建时间倒序）。"""
    limit = max(1, int(limit))
    rows = []
    page = 1
    while len(rows) < limit:
        data = _post(token, "/factory/orderProductBatchNumber/index", {
            "status": "", "order_codes": [], "third_order_ids": "",
            "names": "", "batch_numbers": "", "order_product_line_ids": "",
            "assign_user_id": -2, "page": page, "per_page": min(limit, 100),
        })
        current = data.get("data") or []
        rows.extend(current)
        last_page = int(data.get("last_page") or page)
        if not current or page >= last_page:
            break
        page += 1

    batches = []
    for row in rows[:limit]:
        batch_number = str(row.get("batch_number") or "").strip()
        if not batch_number:
            continue
        progress = row.get("progress") if isinstance(row.get("progress"), dict) else {}
        batches.append({
            "批次号": batch_number,
            "名称": str(row.get("name") or "").strip(),
            "件数": _number(row.get("piece_count"), progress.get("total_num"), row.get("total_num"), row.get("num")),
            "创建时间": str(row.get("created_at") or row.get("created_date") or ""),
        })
    batches.sort(key=lambda batch: batch["创建时间"], reverse=True)
    return batches


def get_batch_order_codes(token, batch_number):
    """返回批次内去重后的订单号（保持接口顺序）。"""
    batch = str(batch_number or "").strip().upper()
    if not batch:
        return []
    codes = []
    seen = set()
    page = 1
    last_page = 1
    while page <= last_page:
        data = _post(token, "/factory/orderProductOrder/getOrderList", {
            "batch_numbers": [batch], "status": -3, "page": page, "per_page": 500,
        })
        for row in data.get("data") or []:
            order = row.get("order_data") if isinstance(row.get("order_data"), dict) else {}
            code = str(order.get("order_code") or "").strip()
            if code and code not in seen:
                codes.append(code)
                seen.add(code)
        last_page = int(data.get("last_page") or page)
        page += 1
    return codes


def _number(*values):
    for value in values:
        try:
            if value not in (None, ""):
                return int(value)
        except (TypeError, ValueError):
            continue
    return 0
