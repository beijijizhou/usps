import requests

try:
    import streamlit as st
except ImportError:
    st = None

DEFAULT_TOKENS = {
    "UV": "2801|0C8LB7C4A7w3jX32PQzyypkG5pO7OovbkcEE8dIid626fe65",
    "T-Shirt": "2799|QlFEGq5olPNbOaWwuPSUOqByxLsG6InHAYmz6cRga8233796",
    "3D": "6704|uu4Q6AiOPEOEEPnipX2K1Oityy2ua32hLNbLf8j5b82b0b63",
}

SHELF_IDS = {
    DEFAULT_TOKENS["UV"]: 206,
    DEFAULT_TOKENS["T-Shirt"]: 194,
    DEFAULT_TOKENS["3D"]: 267,
}


def get_s2b_tokens():
    if st is None:
        return DEFAULT_TOKENS

    try:
        configured_tokens = st.secrets.get("s2b_tokens", {})
    except Exception:
        configured_tokens = {}

    tokens = DEFAULT_TOKENS.copy()
    for label in tokens:
        value = configured_tokens.get(label)
        if value:
            tokens[label] = value
    return tokens


TOKENS = get_s2b_tokens()


def is_success_response(http_status, data):
    if http_status != 200 or not isinstance(data, dict):
        return False

    status_value = data.get("status_code") or data.get("status")
    code_value = data.get("code") or data.get("errcode")
    success_value = data.get("success")

    if success_value is True:
        return True
    if str(status_value).lower() in {"200", "success", "true", "ok"}:
        return True
    if str(code_value) in {"0", "200"}:
        return True

    message = str(data.get("message") or data.get("msg") or "").lower()
    return "success" in message or "成功" in message


def extract_message(data):
    if not isinstance(data, dict):
        return str(data or "")
    return str(
        data.get("message")
        or data.get("msg")
        or data.get("error")
        or data.get("errmsg")
        or data
    )


def push_delivery_print(order_code, token=None):
    """
    Gets print information for the order.
    """
    clean_order_code = str(order_code or "").strip()
    if not clean_order_code:
        return {
            "ok": False,
            "http_status": None,
            "message": "订单号为空",
            "data": None,
        }

    url = (
        "https://overseasfactory.s2bdiy.com/req/factory/delivery/goodsDeliveryPrint"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}"
    }

    params = {
        "code": clean_order_code
    }

    try:
        response = requests.post(
            url,
            params=params,
            headers=headers,
            timeout=10
        )
        try:
            data = response.json()
        except ValueError:
            data = {"message": response.text}

        return {
            "ok": is_success_response(response.status_code, data),
            "http_status": response.status_code,
            "message": extract_message(data),
            "data": data,
        }

    except Exception as e:
        return {
            "ok": False,
            "http_status": None,
            "message": str(e),
            "data": None,
        }


if __name__ == "__main__":
    push_delivery_print("TYLX97", TOKENS["UV"])
