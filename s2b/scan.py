import requests

TOKENS = {
    "UV": "2801|0C8LB7C4A7w3jX32PQzyypkG5pO7OovbkcEE8dIid626fe65",
    "T-Shirt": "2799|QlFEGq5olPNbOaWwuPSUOqByxLsG6InHAYmz6cRga8233796",
    "3D":"6704|uu4Q6AiOPEOEEPnipX2K1Oityy2ua32hLNbLf8j5b82b0b63"
}

SHELF_IDS = {
    TOKENS["UV"]: 206,
    TOKENS["T-Shirt"]: 194,
    TOKENS["3D"]:267
}

def push_delivery_print(order_code, token=None):
    """
    Gets print information for the order.
    """

    url = (
        "https://overseasfactory.s2bdiy.com/req/factory/delivery/goodsDeliveryPrint"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}"
    }

    params = {
        "code": order_code
    }

    try:
        print(f"Getting print info for code: {order_code}...")

        response = requests.post(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data}")
            return data
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"Failed to get print info for {order_code}: {e}")
        return None


if __name__ == "__main__":
    push_delivery_print("TYLX97", TOKENS["UV"])