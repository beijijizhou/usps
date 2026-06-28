USPS_BATCH_SIZE = 35
USPS_TRACKING_URL = "https://tools.usps.com/go/TrackAction"


def build_usps_batch_url(tracking_numbers):
    labels = ",".join(str(num).strip() for num in tracking_numbers if str(num).strip())
    return f"{USPS_TRACKING_URL}?tLabels={labels}"


def build_usps_website_batches(df, batch_size=USPS_BATCH_SIZE):
    df_clean = df.fillna("").astype(str)
    valid_rows = df_clean[df_clean["Tracking Number"].str.strip() != ""]

    batches = []
    mapping_rows = []
    current_tracking_numbers = []
    batch_number = 1
    position_in_batch = 1

    for _, row in valid_rows.iterrows():
        tracking_number = row.get("Tracking Number", "").strip()
        if not tracking_number:
            continue

        current_tracking_numbers.append(tracking_number)
        mapping_rows.append({
            "Batch": batch_number,
            "Position in Batch": position_in_batch,
            "Order ID": row.get("Order ID", "").strip(),
            "Tracking Number": tracking_number,
            "Website Status": "",
            "Notes": ""
        })
        position_in_batch += 1

        if len(current_tracking_numbers) == batch_size:
            batches.append({
                "Batch": batch_number,
                "Count": len(current_tracking_numbers),
                "USPS Batch Link": build_usps_batch_url(current_tracking_numbers)
            })
            batch_number += 1
            position_in_batch = 1
            current_tracking_numbers = []

    if current_tracking_numbers:
        batches.append({
            "Batch": batch_number,
            "Count": len(current_tracking_numbers),
            "USPS Batch Link": build_usps_batch_url(current_tracking_numbers)
        })

    return batches, mapping_rows


def filter_usps_tracking_rows(df):
    if df.empty or "Tracking Number" not in df.columns:
        return df.iloc[0:0].copy()

    df_clean = df.fillna("").astype(str)
    tracking_numbers = df_clean["Tracking Number"].str.strip()
    usps_mask = tracking_numbers.str.startswith("9")

    if "Carrier" in df_clean.columns:
        usps_mask = usps_mask | df_clean["Carrier"].str.upper().str.contains("USPS", na=False)

    return df_clean[usps_mask & (tracking_numbers != "")]
