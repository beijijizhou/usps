import requests
import time
from SDS.headers import get_qa_headers

LABEL_SCAN_URL = "https://pod-api.sdspod.com/pod/qc/factoryOrder/fast"
SUCCESS_CODES = {0, 200, "0", "200", "SUCCESS", "success", True}


def get_headers():
    return get_qa_headers()


def parse_label_scan_response(order_no, response):
    try:
        body = response.json()
    except ValueError:
        body = response.text

    result = {
        "ok": False,
        "order_no": order_no,
        "http_status": response.status_code,
        "api_code": "",
        "message": "",
        "raw": body,
    }

    if response.status_code != 200:
        result["message"] = str(body)
        return result

    if not isinstance(body, dict):
        result["ok"] = True
        result["message"] = str(body)
        return result

    api_code = body.get("code", body.get("status", body.get("success", "")))
    message = body.get("msg", body.get("message", body.get("errorMsg", body.get("error", ""))))
    result["api_code"] = api_code
    result["message"] = str(message or body)

    if body.get("errorMsg"):
        result["ok"] = False
    elif body.get("shipmentInfo") or body.get("printCarriagePdf") == 1:
        result["ok"] = True
        shipment_info = body.get("shipmentInfo") or {}
        tracking_number = shipment_info.get("carriageNo", "")
        pdf_url = shipment_info.get("pdfUrl") or shipment_info.get("laberPdf", "")
        result["message"] = f"出面单成功 {tracking_number}".strip()
        result["tracking"] = tracking_number
        result["pdf_url"] = pdf_url
    elif api_code == "":
        result["ok"] = False
    else:
        result["ok"] = api_code in SUCCESS_CODES

    return result


def scanID(order_no, headers=None):
    """
    Calls the SDS QC fast-scan API to create/scan the shipping label.
    """
    timestamp_ms = int(time.time() * 1000)
    params = {
        "no": order_no,
        "t": timestamp_ms
    }
    request_headers = headers or get_headers()

    if not request_headers.get("access-token"):
        return {
            "ok": False,
            "order_no": order_no,
            "http_status": "",
            "api_code": "",
            "message": "QA token 为空，请检查当前平台的 QA 登录配置。",
            "raw": "",
        }

    try:
        print(f"\nScanning Order: {order_no}...")
        response = requests.get(LABEL_SCAN_URL, params=params, headers=request_headers, timeout=10)
        result = parse_label_scan_response(order_no, response)
        print(f"QC Scan Result: {result}")
        return result
            
    except Exception as e:
        print(f"Scan failed: {e}")
        return {
            "ok": False,
            "order_no": order_no,
            "http_status": "",
            "api_code": "",
            "message": str(e),
            "raw": "",
        }


def run_batch_scan(ids):
    scan_results = []
    print(f"Starting batch scan for {len(ids)} orders...")
    
    for i, order_no in enumerate(ids, 1):
        # Call your existing scanID function
        result = scanID(order_no)
        
        if result and result.get("ok"):
            scan_results.append({"order_no": order_no, "data": result})
            print(f"[{i}/{len(ids)}] Successfully scanned {order_no}")
        else:
            print(f"[{i}/{len(ids)}] Failed to scan {order_no}")
            
    return scan_results
