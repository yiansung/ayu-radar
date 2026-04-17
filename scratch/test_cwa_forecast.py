import requests
import os
from dotenv import load_dotenv

load_dotenv()
CWA_TOKEN = os.getenv('CWA_TOKEN')

def test_cwa_forecast():
    # F-D0047-071: 新北市各鄉鎮市區3天電力天氣預報
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-071?Authorization={CWA_TOKEN}&format=JSON"
    try:
        response = requests.get(url)
        data = response.json()
        locations = data['records']['locations'][0]['location']
        
        for loc in locations:
            name = loc['locationName']
            if name in ['坪林區', '烏來區']:
                print(f"Found: {name}")
                # We need PoP12h for rainfall probability
                for elem in loc['weatherElement']:
                    if elem['elementName'] in ['PoP12h', 'Wx']:
                        print(f"  Element: {elem['elementName']}")
                        # Just print the first 2 time slots for preview
                        for time in elem['time'][:2]:
                            print(f"    Start: {time['startTime']}, Value: {time['elementValue'][0]['value']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if not CWA_TOKEN:
        print("No CWA_TOKEN found in .env")
    else:
        test_cwa_forecast()
