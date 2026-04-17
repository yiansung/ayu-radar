import urllib.request
import json
import os

def check_keys_deep():
    token = os.environ.get('CWA_TOKEN')
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-071?Authorization={token}&format=JSON"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            records = data.get('records', {})
            # It's 'Locations' (Capital)
            locations_group = records.get('Locations', [])
            if locations_group:
                location_list = locations_group[0].get('Location', []) # Is it Location (Capital) too?
                if not location_list:
                    print(f"Location group keys: {list(locations_group[0].keys())}")
                    # Checking if it's 'location' (lowercase) inside 'Locations'
                    location_list = locations_group[0].get('location', [])
                
                if location_list:
                    for loc in location_list:
                        if "坪林" in loc['LocationName'] or "坪林" in loc.get('locationName', ''):
                            print(f"Found Town: {loc.get('LocationName') or loc.get('locationName')}")
                            elems = loc.get('WeatherElement', []) or loc.get('weatherElement', [])
                            print(f"WeatherElement keys: {list(elems[0].keys()) if elems else 'None'}")
                            for el in elems:
                                if el.get('ElementName') == 'PoP12h' or el.get('elementName') == 'PoP12h':
                                    time_slot = el.get('Time', [{}])[0] or el.get('time', [{}])[0]
                                    print(f"Time slot keys: {list(time_slot.keys())}")
                                    val_obj = time_slot.get('ElementValue', [{}])[0] or time_slot.get('elementValue', [{}])[0]
                                    print(f"Value object keys: {list(val_obj.keys())}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_keys_deep()
