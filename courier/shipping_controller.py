import time
# Ensure these imports match your filenames exactly (e.g., gofo_courier.py)
from courier.gofo_courier import GofoCourier
from courier.usps_courier import UspsCourier

def run_shipping_controller(df, courier_name, progress_bar, status_text):
    df_clean = df.fillna("").astype(str)
    
    # 1. Selection & Initialization (Injecting the map here)
    if courier_name == "GOFO":
        valid_df = df_clean[df_clean["Tracking Number"].str.startswith("GF")]
        specific_map = dict(zip(valid_df["Tracking Number"], valid_df["Order ID"]))
        handler = GofoCourier(specific_map)
        
    elif courier_name == "USPS":
        # USPS filter: starts with 9 and has a reasonable length
        valid_df = df_clean[
            (df_clean["Tracking Number"].str.startswith("9")) & 
            (df_clean["Tracking Number"].str.len() >= 20)
        ]
        specific_map = dict(zip(valid_df["Tracking Number"], valid_df["Order ID"]))
        handler = UspsCourier(specific_map)
    else:
        return []

    tracking_list = valid_df["Tracking Number"].tolist()
    total = len(tracking_list)
    
    if total == 0:
        return []

    all_results = []
    batch_size = 35

    # 2. Batch Loop
    for i in range(0, total, batch_size):
        batch = tracking_list[i : i + batch_size]
        
        # UI Feedback
        percent = i / total
        if progress_bar:
            progress_bar.progress(percent, text=f"{courier_name} {int(percent*100)}%")
        if status_text:
            status_text.info(f"Requesting {i}/{total} from {courier_name}...")
        
        # 3. Execution (The map is already inside the handler instance)
        batch_results = handler.track(batch)
        all_results.extend(batch_results)
        
        time.sleep(0.1)

    # Finalize UI for this courier
    if progress_bar:
        progress_bar.progress(1.0, text=f"{courier_name} 100%")

    return all_results