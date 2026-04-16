import requests
import json
import os
from dotenv import load_dotenv

load_dotenv('/Users/yiansung/Documents/MD/AyuFishingApp/backend/.env')
CWA_TOKEN = os.getenv('CWA_TOKEN')

url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={CWA_TOKEN}&StationId=C0A530"

resp = requests.get(url)
data = resp.json()

print(json.dumps(data, indent=2, ensure_ascii=False))
