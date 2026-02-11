import requests

url = "https://cps-api.robotees.us/cps/web/base-shirt-stock/page"
sso_token = "eyJzb3VyY2UiOiJTU08iLCJhbGciOiJSUzI1NiJ9.eyJtdCI6MSwic3NvVXNlciI6IntcInJlYWxOYW1lXCI6XCJoYWxvb3BuZ1wiLFwidXNlcklkXCI6NzExNTY0Njc3LFwidXNlckNvZGVcIjpcIjAxMDAwMDM5MDAwMDFcIixcInVzZXJuYW1lXCI6XCJoYWxvb3BuZ1wifSIsImp0aSI6IlptUm1aV0V3WXpFdE9ESXdOUzAwWmpaaExUZzBOall0WXpFNVkyWTFNRE0yTUdRdyIsImV4cCI6MTc3MTQ0Mzk3N30.BzUjga09LnGn1UlRPUv4stAtV11TXvoiAYKkpVzWFHiYMdlmdmqjuDEVuCGK50cD8xmbU_zJU9rJofqs_zY5Ztle5Wh05LvWUq6TiWHvfFjyRn4H6ZUTmH1ayTAJeg0SwSqTA1Tn885CCwg_lm7lz7Tu_mrmkWK2xvef0SLGQeCmyccrbaQb9Q--s8xaxWn1AUeQBfvhX0Cn52uiZRHnfYq2tS_Wr1b4WucgoSThvsdD1U_urumTn_5v8nr6HvHd-7m5TTZgsaFKY1iRCFHHDoWxLt7L-aO1FgDR3uY5lYxI_7MCkTXHWMsjzAx8pFclCz3AodmKCYkgbmcsOyBAKg" # Paste your full token here

headers = {
    "Content-Type": "application/json",
    "ssotoken": sso_token,
    "clientid": "a4a8a792eadfb55b",
    "tenant-id": "1000035",
    "systemcode": "CPS"
}

payload = {
    "pageNum": 1,
    "pageSize": 200,
    "spuCodeList": [],
    "skcCodeList": [],
    "skuCodeList": []
}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    print("Success:", response.json())
else:
    print(f"Error {response.status_code}: {response.text}")