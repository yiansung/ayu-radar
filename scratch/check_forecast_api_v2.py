import requests
import json
import os

def check_forecast_api():
    token = os.environ.get('CWA_TOKEN')
    if not token:
        print("Error: No CWA_TOKEN found")
        return

    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-071?Authorization={token}&format=JSON"
    
    try:
        resp = requests.get(url, timeout=10, verify=False)
        data = resp.json()
        print(f"Success: {data.get('success')}")
        
        # Print top level keys
        print(f"Top Keys: {list(data.get('records', {}).keys())}")
        
        locations = data.get('records', {}).get('locations', [])
        if not locations:
            print("No locations found in records.")
            return
            
        location_list = locations[0].get('location', [])
        print(f"Found {len(location_list)} locations.")
        
        for loc in location_list:
            if "坪林" in loc['locationName'] or "烏來" in loc['locationName']:
                print(f"Match: {loc['locationName']}")
                for elem in loc.get('weatherElement', []):
                    if elem['elementName'] in ['PoP12h', 'Wx']:
                        print(f"  {elem['elementName']}: {elem['time'][0]['elementValue'][0]}")
                        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_forecast_api()
