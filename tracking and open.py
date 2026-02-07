import requests
import time
import webbrowser  # Added this to handle browser automation

# --- CONFIGURATION ---
URL = "https://factory.s2bdiy.com/req/factory/order/index"
# TOKEN = "808965|hSN8857AOAANqumfi7AWup0mMjtxyh4GR8n6GUTh"
TOKEN = "813819|rHilycsLrEX33hMVNRnmmtp22OckM2Rf7KdXW8aX"
HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def process_by_page():
    current_page = 1
    total_found = 0
    print("🚀 Starting Streaming Fetch & Auto-Open...")

    while True:
        # USPS limit is 35, so we keep limit at 35
        payload = {
            "page": current_page, 
            "limit": 35, 
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
                print("\n🏁 Reached the end of the order list.")
                break

            page_tracks = []
            for order in orders:
                track = order.get('order_logistics', {}).get('logisticss_track_number')
                if track and str(track).startswith('9'):
                    page_tracks.append(str(track))

            if page_tracks:
                total_found += len(page_tracks)
                bulk_url = f"https://tools.usps.com/go/TrackAction?tLabels={','.join(page_tracks)}"
                
                print(f"\n📄 [ PAGE {current_page} - {len(page_tracks)} USPS Tracks ]")
                print(f"🌍 Opening in browser: {bulk_url}")
                
                # THIS LINE OPENS THE TAB
                webbrowser.open(bulk_url)
            else:
                print(f"ℹ️  Page {current_page}: No USPS tracking numbers found.")

            last_page = data_section.get('last_page', 1)
            if current_page >= last_page:
                break
            
            current_page += 1
            
            # INCREASE THIS SLEEP if you don't want 10 tabs opening in 2 seconds
            # A 2 or 3 second delay gives you time to look at the tabs as they appear
            time.sleep(2) 

        except Exception as e:
            print(f"⚠️  Critical Error: {e}")
            break

    print(f"\n✅ All done! Total USPS numbers processed: {total_found}")

if __name__ == "__main__":
    process_by_page()