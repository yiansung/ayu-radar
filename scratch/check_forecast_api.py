import urllib.request
import json
import os

def check_forecast_api():
    token = os.environ.get('CWA_TOKEN')
    if not token:
        print("Error: No CWA_TOKEN found")
        return

    # F-D0047-071 (New Taipei City)
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-071?Authorization={token}&format=JSON"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            locations = data.get('records', {}).get('locations', [])[0].get('location', [])
            for loc in locations:
                if "坪林" in loc['locationName'] or "烏來" in loc['locationName']:
                    print(f"Found: {loc['locationName']}")
                    for elem in loc.get('weatherElement', []):
                        if elem['elementName'] in ['PoP12h', 'Wx']:
                            print(f"  Element: {elem['elementName']}")
                            # print(elem['time'][0])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_forecast_api()
