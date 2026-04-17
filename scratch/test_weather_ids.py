import requests
import os
import json

def test_weather_endpoints():
    token = "CWA-521ECC48-08A3-4A55-BD04-F31E82B5DAED"
    # Pinglin CAAD90, Wulai C2A560
    for sid, cwa_id in [("pinglin", "CAAD90"), ("wulai", "C2A560")]:
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={token}&format=JSON&StationId={cwa_id}"
        print(f"Testing {sid} ({cwa_id}) URL: {url}")
        try:
            resp = requests.get(url, timeout=10, verify=False)
            print(f"Status: {resp.status_code}")
            data = resp.json()
            if data.get('success') == 'true' and data['records']['Station']:
                print(f"✅ Success! Station: {data['records']['Station'][0]['StationName']}")
            else:
                print(f"⚠️ No data returned. Success field: {data.get('success')}")
                if 'records' in data:
                    print(f"Records keys: {list(data['records'].keys())}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_weather_endpoints()
