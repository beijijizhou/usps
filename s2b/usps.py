import requests
import time

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
    print("🚀 Starting Streaming Fetch (Page-by-Page)...")

    while True:
        # We fetch 35 per page to match the USPS single-click limit perfectly
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

            # --- PROCESS CURRENT PAGE IMMEDIATELY ---
            page_tracks = []
            for order in orders:
                track = order.get('order_logistics', {}).get('logisticss_track_number')
                if track and str(track).startswith('9'):
                    page_tracks.append(str(track))

            if page_tracks:
                total_found += len(page_tracks)
                bulk_url = f"https://tools.usps.com/go/TrackAction?tLabels={','.join(page_tracks)}"
                
                print(f"\n📄 [ PAGE {current_page} - {len(page_tracks)} USPS Tracks ]")
                print(f"🔗 Bulk Link: {bulk_url}")
            else:
                print(f"ℹ️  Page {current_page}: No USPS tracking numbers found.")

            # Check if we are on the last page according to the API
            last_page = data_section.get('last_page', 1)
            if current_page >= last_page:
                break
            
            # Move to next page
            current_page += 1
            
            # Short safety pause to prevent server-side rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"⚠️  Critical Error: {e}")
            break

    print(f"\n✅ All done! Total USPS numbers processed: {total_found}")

if __name__ == "__main__":
    process_by_page()