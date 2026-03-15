import requests
from courier.base_courier import BaseCourier

class GofoCourier(BaseCourier):
    def track(self, numbers,order_map):
        url = "https://www.gofo.com/us/cnee-api/consignee/track/query"
        payload = {"numberList": numbers}
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            "Referer": "https://www.gofo.com/us/consignee/track"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            data = response.json()
            
            results = []
            # Mapping GOFO keys to our standard keys
            for item in data.get('success', []):
                last_event = item.get('lastTrackEvent', {})
                results.append({
                    "number": item.get('waybillNo'),
                    "status": last_event.get('processContent', 'Unknown'),
                    "time": last_event.get('processDate', 'N/A')
                })
            return results
        except Exception as e:
            print(f"GOFO API Error: {e}")
            return []