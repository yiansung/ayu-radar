import os
import json
from app import app, db, Basin, RiverSection, FishingSpot, Report

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')
REPORTS_FILE = os.path.join(os.path.dirname(__file__), 'reports.json')

def migrate():
    with app.app_context():
        print("--- Initializing Database ---")
        db.create_all()

        # 1. Migrate Basins and Spots
        if os.path.exists(DATA_FILE):
            print(f"Reading {DATA_FILE}...")
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for b_id, b_data in data.items():
                # Create Basin
                basin = Basin.query.get(b_id)
                if not basin:
                    basin = Basin(
                        id=b_id,
                        name=b_data['basin_system'].split('・')[0], # Simplify name
                        weather_station_id=b_data['weather_station_id'],
                        weather_station_name=b_data['weather_station_name']
                    )
                    db.session.add(basin)
                
                # Create Sections and Spots
                for sec in b_data['river_sections']:
                    section = RiverSection(
                        basin_id=b_id,
                        section_id=sec['section_id'],
                        name=sec['name'],
                        section_type=sec['type'],
                        water_level_station_id=sec['water_level_station_id'],
                        water_level_station_name=sec['water_level_station_name'],
                        characteristics=sec['characteristics']
                    )
                    db.session.add(section)
                    db.session.flush() # Get section.id for foreign key

                    for spot in sec['fishing_spots']:
                        f_spot = FishingSpot(
                            section_id=section.id,
                            spot_name=spot['spot_name'],
                            spot_desc=spot['spot_desc'],
                            access_info=spot['access_info'],
                            business_status=spot['business_status'],
                            has_decoy=spot['has_decoy'],
                            decoy_vendor=spot.get('decoy_vendor')
                        )
                        db.session.add(f_spot)

        # 2. Migrate Reports
        if os.path.exists(REPORTS_FILE):
            print(f"Reading {REPORTS_FILE}...")
            with open(REPORTS_FILE, 'r', encoding='utf-8') as f:
                reports_data = json.load(f)
            
            for r in reports_data:
                # Check if exists
                existing = Report.query.get(r['id'])
                if not existing:
                    report = Report(
                        id=r['id'],
                        basin_id=r['basin_id'],
                        spot_name=r['spot_name'],
                        author=r['author'],
                        date=r['date'],
                        status=r['status'],
                        content=r['content'],
                        photo_urls=r['photo_urls'],
                        catch_count=r['catch'].get('count'),
                        catch_max_size=r['catch'].get('max_size'),
                        rod=r['tackle'].get('rod'),
                        line=r['tackle'].get('line'),
                        hook=r['tackle'].get('hook'),
                        water_level=r['telemetry'].get('water_level'),
                        turbidity=r['telemetry'].get('turbidity'),
                        weather_desc=r['telemetry'].get('weather_desc'),
                        temp=r['telemetry'].get('temp')
                    )
                    db.session.add(report)

        db.session.commit()
        print("--- Migration Completed Successfully ---")

if __name__ == "__main__":
    migrate()
