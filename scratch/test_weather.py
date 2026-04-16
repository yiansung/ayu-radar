import urllib.request
import json

token = "CWA-521ECC48-08A3-4A55-BD04-F31E82B5DAED"
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={token}&StationId=CAAD90"

req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))
    
obs = data['records']['Station'][0]
we = obs.get('WeatherElement', {})

weather_desc = we.get('Weather', "晴時多雲")
rain_now_str = we.get('Now', {}).get('Precipitation', "0.0") if isinstance(we.get('Now'), dict) else "0.0"

try:
    rain_now = float(rain_now_str) if rain_now_str != "-99" else 0.0
except:
    rain_now = 0.0

if weather_desc == "-99" or not weather_desc:
    weather_desc = "降雨中 🌧️" if rain_now > 0 else "晴朗多雲"
elif rain_now > 0 and "雨" not in weather_desc:
    weather_desc = "降雨中 🌧️"

temp_str = we.get('AirTemperature', "25.0")
temp = float(temp_str) if temp_str != "-99" and temp_str else 25.0

print(f"Temp: {temp}, Weather: {weather_desc}, Rain: {rain_now}")
