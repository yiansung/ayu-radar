import os
import json
from backend.app import app

def test_api():
    client = app.test_client()
    
    print("Testing /api/live/weather/C0A520 (Pinglin)...")
    resp = client.get('/api/live/weather/C0A520')
    print(f"Status: {resp.status_code}, Data: {resp.json.get('station_name')}")
    
    print("Testing /api/live/weather/C0A560 (Wulai)...")
    resp = client.get('/api/live/weather/C0A560')
    print(f"Status: {resp.status_code}, Data: {resp.json.get('station_name')}")
    
    print("Testing /api/live/water/1140H048 (Pinglin)...")
    resp = client.get('/api/live/water/1140H048')
    print(f"Status: {resp.status_code}, Data: {resp.json.get('station_name')}")
    
    print("Testing /api/live/water/1140H096 (Wulai)...")
    resp = client.get('/api/live/water/1140H096')
    print(f"Status: {resp.status_code}, Data: {resp.json.get('station_name')}")
    
    print("Testing /api/fishing_spots/pinglin...")
    resp = client.get('/api/fishing_spots/pinglin')
    print(f"Status: {resp.status_code}, Sections: {len(resp.json.get('river_sections', []))}")
    
    print("Testing /api/fishing_spots/wulai...")
    resp = client.get('/api/fishing_spots/wulai')
    print(f"Status: {resp.status_code}, Sections: {len(resp.json.get('river_sections', []))}")

if __name__ == "__main__":
    test_api()
