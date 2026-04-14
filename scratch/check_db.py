import os
import json
from backend.app import app, db, Basin, RiverSection, FishingSpot

with app.app_context():
    print(f"Basins: {Basin.query.count()}")
    for b in Basin.query.all():
        print(f"  Basin: {b.id} ({b.name}), Weather Station: {b.weather_station_id}")
        for s in b.sections:
            print(f"    Section: {s.name} (ID: {s.id}, Basin: {s.basin_id}, Type: {s.section_type}, Station: {s.water_level_station_id})")
            print(f"    Spots: {len(s.spots)}")
            for spot in s.spots:
                print(f"      - {spot.spot_name} (has_decoy: {spot.has_decoy})")
