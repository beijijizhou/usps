import time
from gofo_utils import track_gofo_web_api

def parse_gofo_contents(api_response):
    """
    Parses the raw JSON to extract only tracking numbers 
    and their processContent.
    """
    extracted = []
    # api_response is usually a list based on your previous output
    for root in api_response:
        data_list = root.get('data', [])["success"]
        
        for entry in data_list:
            waybill = entry.get('waybillNo')
            last_event = entry.get('lastTrackEvent', {})
            content = last_event.get('processContent', 'Unknown')
            extracted.append({"number": waybill, "content": content})
    return extracted

def run_tracking_pipeline(raw_numbers_str, chunk_size=100):
    """
    The main logic to be used in production.
    """
    # 1. Clean
    full_list = [t.strip() for t in raw_numbers_str.split(',') if t.strip()]
    all_raw_results = []

    # 2. Execute
    for i in range(0, len(full_list), chunk_size):
        chunk = full_list[i : i + chunk_size]
        response = track_gofo_web_api(chunk)
        
        if "error" in response and not isinstance(response, list):
            return {"error": response["error"]}
            
        all_raw_results.append(response)
        if i + chunk_size < len(full_list):
            time.sleep(0.1)

    # 3. Parse only what we need
    return parse_gofo_contents(all_raw_results)

def main():
    # Example input
    raw_input = "GFUS01039289273025,GFUS01039289268801,GFUS01039289271552,GFUS01039289270657,GFUS01039289270977,GFUS01039241536192,GFUS01039264818816,GFUS01039264830530,GFUS01039264813568,GFUS01039264823104,GFUS01039264823745,GFUS01039264813762,GFUS01039264820288,GFUS01039264801345,GFUS01039264803520,GFUS01039241536770,GFUS01039264801344,GFUS01039241536578,GFUS01039264813440,GFUS01039264825728,GFUS01039264842433,GFUS01039264816770,GFUS01039264797120,GFUS01039264827392,GFUS01039264794624,GFUS01039264836673,GFUS01039264818433,GFUS01039264858113,GFUS01039264818305,GFUS01039241535680,GFUS01039264810112,GFUS01039241536771,GFUS01039264813825,GFUS01039264797761,GFUS01039264801921,GFUS01039241536768,GFUS01039264802112,GFUS01039264819200,GFUS01039264840833,GFUS01039264805954,GFUS01039264821635,GFUS01039264811200,GFUS01039264811008,GFUS01039264802817,GFUS01039264824065,GFUS01039264842881,GFUS01039264820544,GFUS01039264843968,GFUS01039264798531,GFUS01039264800064,GFUS01039264817345,GFUS01039264826048,GFUS01039241535872,GFUS01039264801856,GFUS01039264819968,GFUS01039264828480,GFUS01039264809666,GFUS01039264820482,GFUS01039264792769,GFUS01039264797056,GFUS01039264793280,GFUS01039264816961,GFUS01039264866498,GFUS01039264815616,GFUS01039264799808,GFUS01039264793344,GFUS01039264824001,GFUS01039264795009,GFUS01039241535936,GFUS01039241536000,GFUS01039264801282,GFUS01039241536257,GFUS01039264805312,GFUS01039264813504,GFUS01039264812674,GFUS01039264802048,GFUS01039241536640,GFUS01039264817857,GFUS01039241535940,GFUS01039264806913,GFUS01039264858497,GFUS01039241535489,GFUS01039241605889,GFUS01039241536065,GFUS01039241536642,GFUS01039241536258,GFUS01039241536577,GFUS01039241535488,GFUS01039241537346,GFUS01039241536833,GFUS01039289274178,GFUS01039264811585,GFUS01039241537345,GFUS01039241536641,GFUS01039241536643,GFUS01039241536002,GFUS01039241536064,GFUS01039241535490,GFUS01039241536579,GFUS01039241536832"
    
    # Run the single logic function
    results = run_tracking_pipeline(raw_input)
    
    # Display results
    if isinstance(results, list):
        for item in results:
            print(f"📦 {item['number']}: {item['content']}")
    else:
        print(f"❌ Pipeline Error: {results.get('error')}")

if __name__ == "__main__":
    main()