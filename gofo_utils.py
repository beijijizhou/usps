import requests
def track_gofo_web_api(tracking_numbers):
    # The URL you found in the browser
    url = "https://www.gofo.com/us/cnee-api/consignee/track/query"
    
    # The payload structure must match exactly what the website sends
    payload = {
        "numberList": tracking_numbers  # Pass a list of strings
    }
    
    # Websites often check for 'User-Agent' and 'Referer' to block bots.
    # Mimicking a real browser header is highly recommended.
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.gofo.com/us/consignee/track",
        "Origin": "https://www.gofo.com"
    }

    try:
        # Use .post() because you are sending a payload
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # Check if the request was successful
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Example Usage:
