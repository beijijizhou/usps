def build_scan_log_row(scan_result, label_scan_result=None):
    order_id = scan_result.get("Order ID")
    success = scan_result.get("status") == "success"
    tracking_number = scan_result.get("tracking", "")
    msg = scan_result.get("msg") or tracking_number
    carrier_name = scan_result.get("carrier", "")

    if success and "USPS" in carrier_name:
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
        "Label Scan": "✅ Scanned" if label_scan_result else "❌ Scan Failed",
        "Scan Status": scan_status,
        "Result": result
    }
