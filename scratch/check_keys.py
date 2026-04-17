import urllib.request
import json
import os

def check_keys():
    token = os.environ.get('CWA_TOKEN')
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-071?Authorization={token}&format=JSON"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"Top Keys: {list(data.keys())}")
            if 'records' in data:
                print(f"Records Keys: {list(data['records'].keys())}")
                if 'locations' in data['records']:
                    # Some versions have locations as a list, some as an object
                    locs = data['records']['locations']
                    print(f"Locations Type: {type(locs)}")
                    if isinstance(locs, list) and len(locs) > 0:
                        print(f"First Location Group Keys: {list(locs[0].keys())}")
                        if 'location' in locs[0]:
                            print(f"Number of distinct towns: {len(locs[0]['location'])}")
                            print(f"Sample town: {locs[0]['location'][0]['locationName']}")
                # Alternative: maybe it is just 'location'?
                if 'location' in data['records']:
                    print("Found 'location' directly under 'records'")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_keys()
