from SDS.QA_scan import scanID


def build_scan_log_row(scan_result):
    order_id = scan_result.get("Order ID")
    success = scan_result.get("status") == "success"
    tracking_number = scan_result.get("tracking", "")
    msg = scan_result.get("msg") or tracking_number
    carrier_name = scan_result.get("carrier", "")

    if success and carrier_name == "USPS":
        scanID(order_id)
        scan_status = "✅ Success (USPS)"
        result = msg
    elif success:
        scan_status = "⚠️ Skipped"
        result = f"Non-USPS carrier: {carrier_name}"
    else:
        scan_status = "❌ Failed"
        result = msg

    return {
        "Order ID": order_id,
        "Tracking Number": tracking_number,
        "Carrier": carrier_name,
        "Scan Status": scan_status,
        "Result": result
    }
