import requests
import time
import webbrowser

# --- CONFIGURATION ---
URL = "https://factory.s2bdiy.com/req/factory/order/index"
# TOKEN = "808965|hSN8857AOAANqumfi7AWup0mMjtxyh4GR8n6GUTh"
TOKEN = "813819|rHilycsLrEX33hMVNRnmmtp22OckM2Rf7KdXW8aX"
HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def process_in_batches_of_35():
    current_page = 1
    total_processed = 0
    buffer = []  # This will store numbers until we hit 35
    
    print("🚀 Gathering USPS tracks in batches of 35...")

    while True:
        # We fetch 100 per page from the factory to find USPS numbers faster
        payload = {
            "page": current_page, 
            "limit": 100, 
            "status": 4
        }
        
        try:
            response = requests.post(URL, headers=HEADERS, json=payload, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Error on Page {current_page}: {response.status_code}")
                break
            
            res_json = response.json()
            data_section = res_json.get('data', {})
            orders = data_section.get('data', [])

            if not orders:
                # If we finish all pages but still have leftover numbers in the buffer
                if buffer:
                    open_usps(buffer)
                print("\n🏁 Reached the end of all orders.")
                break

            # Filter for USPS numbers
            for order in orders:
                track = order.get('order_logistics', {}).get('logisticss_track_number')
                if track and str(track).startswith('9'):
                    buffer.append(str(track))
                    
                    # AS SOON AS WE HIT 35, OPEN THE LINK
                    if len(buffer) == 35:
                        open_usps(buffer)
                        total_processed += 35
                        buffer = [] # Clear the buffer for the next batch
                        time.sleep(2) # Delay to not overwhelm the browser

            last_page = data_section.get('last_page', 1)
            if current_page >= last_page:
                if buffer: # Handle the final leftover batch
                    open_usps(buffer)
                    total_processed += len(buffer)
                break
            
            current_page += 1

        except Exception as e:
            print(f"⚠️  Critical Error: {e}")
            break

    print(f"\n✅ All done! Total USPS numbers opened: {total_processed}")

def open_usps(track_list):
    """Helper function to format the URL and open the browser"""
    bulk_url = f"https://tools.usps.com/go/TrackAction?tLabels={','.join(track_list)}"
    print(f"🌍 Opening Batch of {len(track_list)} tracks...")
    webbrowser.open(bulk_url)

if __name__ == "__main__":
    process_in_batches_of_35()