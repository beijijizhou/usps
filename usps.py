import requests
import time

# --- CONFIGURATION ---
URL = "https://factory.s2bdiy.com/req/factory/order/index"
TOKEN = "808965|hSN8857AOAANqumfi7AWup0mMjtxyh4GR8n6GUTh"
HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0'
}

def get_all_usps_numbers():
    all_tracks = []
    current_page = 1
    print("🛰️  Fetching tracking numbers from factory...")
    
    while True:
        payload = {"page": current_page, "limit": 100, "status": 4}
        try:
            response = requests.post(URL, headers=HEADERS, json=payload, timeout=10)
            if response.status_code != 200: break
            
            data_section = response.json().get('data', {})
            orders = data_section.get('data', [])
            if not orders: break

            for order in orders:
                track = order.get('order_logistics', {}).get('logisticss_track_number')
                # Filter for USPS starting with 9
                if track and str(track).startswith('9'):
                    all_tracks.append(str(track))

            if current_page >= data_section.get('last_page', 1): break
            current_page += 1
        except Exception as e:
            print(f"Error: {e}")
            break
    return list(set(all_tracks)) # Remove duplicates

def track_status_sim(tracking_list):
    """
    Chunks numbers into 35 and provides a direct tracking link 
    for bulk checking.
    """
    chunk_size = 35
    total = len(tracking_list)
    print(f"\n✅ Total USPS Numbers Collected: {total}")
    
    for i in range(0, total, chunk_size):
        chunk = tracking_list[i : i + chunk_size]
        batch_num = int(i/chunk_size) + 1
        
        # Create a bulk tracking URL for USPS (Standard format)
        # Note: USPS website allows multiple numbers separated by commas
        bulk_url = f"https://tools.usps.com/go/TrackAction?tLabels={','.join(chunk)}"
        
        print(f"\n--- [ BATCH {batch_num} ] ---")
        print(f"Numbers: {len(chunk)}")
        print(f"🔗 Click to track this batch: \n{bulk_url}")

# Run the process
if __name__ == "__main__":
    usps_numbers = get_all_usps_numbers()
    if usps_numbers:
        track_status_sim(usps_numbers)
    else:
        print("❌ No USPS numbers found.")