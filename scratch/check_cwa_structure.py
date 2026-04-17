import urllib.request
import json
import os

def test_forecast_structure():
    token = os.environ.get('CWA_TOKEN')
    if not token:
        print("Error: No CWA_TOKEN found")
        return

    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-071?Authorization={token}&format=JSON&locationName=%E5%9D%AA%E6%9E%97%E5%8D%80"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_forecast_structure()
