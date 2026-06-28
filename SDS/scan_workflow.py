def build_scan_log_row(scan_result, label_scan_result=None):
    order_id = scan_result.get("Order ID")
    success = scan_result.get("status") == "success"
    tracking_number = scan_result.get("tracking", "")
    msg = scan_result.get("msg") or tracking_number
    carrier_name = scan_result.get("carrier", "")

    if success and "USPS" in carrier_name:
        scan_status = "✅ 成功（USPS）"
        result = msg
    elif success:
        scan_status = "⚠️ 已跳过"
        result = f"非 USPS 渠道：{carrier_name}"
    else:
        scan_status = "❌ 失败"
        result = msg

    return {
        "Order ID": order_id,
        "Tracking Number": tracking_number,
        "Carrier": carrier_name,
        "Label Scan": "✅ 已出面单" if label_scan_result else "❌ 出面单失败",
        "Scan Status": scan_status,
        "Result": result
    }
