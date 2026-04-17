import urllib.request
import json
import os

def check_forecast_api():
    token = os.environ.get('CWA_TOKEN')
    if not token:
        print("Error: No CWA_TOKEN found")
        return

    # F-D0047-071
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-071?Authorization={token}&format=JSON"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"Success: {data.get('success')}")
            
            locations = data.get('records', {}).get('locations', [])
            if not locations:
                print("No locations found.")
                return
                
            location_list = locations[0].get('location', [])
            for loc in location_list:
                if "坪林" in loc['locationName']:
                    print(f"Match Town: {loc['locationName']}")
                    for elem in loc.get('weatherElement', []):
                        if elem['elementName'] in ['PoP12h', 'Wx']:
                            print(f"  {elem['elementName']} First Time Slot:")
                            print(f"    {elem['time'][0]['elementValue'][0]}")
                            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_forecast_api()
