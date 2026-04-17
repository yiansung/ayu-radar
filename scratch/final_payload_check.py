import urllib.request
import json
import os

def final_payload_check():
    token = os.environ.get('CWA_TOKEN')
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-071?Authorization={token}&format=JSON"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            loc_group = data['records']['Locations'][0]
            # Find Pinglin
            pinglin = next(l for l in loc_group['Location'] if "坪林" in l['LocationName'])
            pop12h = next(e for e in pinglin['WeatherElement'] if e['ElementName'] == 'PoP12h')
            # Look at the first time slot value
            print(f"Value Structure: {pinglin['WeatherElement'][0]['Time'][0]['ElementValue'][0]}")
            # print first 3 town names to be sure
            print(f"Sample Towns: {[l['LocationName'] for l in loc_group['Location'][:3]]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    final_payload_check()
