import urllib.request
import json
import os

def check_rain_keys():
    token = os.environ.get('CWA_TOKEN')
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001?Authorization={token}&format=JSON&StationId=C0A530"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            station = data['records']['Station'][0]
            print(f"Station: {station['StationName']}")
            re = station.get('RainfallElement', {})
            print(f"RainfallElement Keys: {list(re.keys())}")
            for period in ['Past24hr', 'Past3days', 'past24hr', 'past3days']:
                if period in re:
                    print(f"  {period}: {re[period]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_rain_keys()
