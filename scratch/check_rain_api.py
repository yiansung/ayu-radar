import urllib.request
import json
import os

def check_rain_api():
    token = os.environ.get('CWA_TOKEN')
    if not token:
        print("Error: No CWA_TOKEN found")
        return

    # Using C0A530 (Pinglin)
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001?Authorization={token}&StationId=C0A530"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_rain_api()
