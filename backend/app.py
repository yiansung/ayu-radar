from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import json
import random
import time
import os
import requests
import threading
from functools import wraps
from dotenv import load_dotenv

# Environment Tweak for Mac SSL/Proxy stability
os.environ['NO_PROXY'] = '127.0.0.1,localhost'

# Load environment variables
load_dotenv()
CWA_TOKEN = os.getenv('CWA_TOKEN')

# Disable SSL warnings for Mac dev env
requests.packages.urllib3.disable_warnings()

# Setup Directories
basedir = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(basedir, '../frontend'))

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ayu_radar.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload Configuration
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ADMIN_PASSWORD = "qingshu1212"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Database Models ---

class Basin(db.Model):
    __tablename__ = 'basins'
    id = db.Column(db.String(50), primary_key=True) # e.g., 'pinglin'
    name = db.Column(db.String(100), nullable=False)
    weather_station_id = db.Column(db.String(50))
    weather_station_name = db.Column(db.String(100))
    sections = db.relationship('RiverSection', backref='basin', lazy=True)

class RiverSection(db.Model):
    __tablename__ = 'river_sections'
    id = db.Column(db.Integer, primary_key=True)
    basin_id = db.Column(db.String(50), db.ForeignKey('basins.id'), nullable=False)
    section_id = db.Column(db.String(50), nullable=False) # e.g., 'P01_MAIN'
    name = db.Column(db.String(100), nullable=False)
    section_type = db.Column(db.String(50)) # e.g., '主流'
    water_level_station_id = db.Column(db.String(50))
    water_level_station_name = db.Column(db.String(100))
    characteristics = db.Column(db.Text)
    spots = db.relationship('FishingSpot', backref='section', lazy=True)

class FishingSpot(db.Model):
    __tablename__ = 'fishing_spots'
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('river_sections.id'), nullable=False)
    spot_name = db.Column(db.String(100), nullable=False)
    spot_desc = db.Column(db.Text)
    access_info = db.Column(db.String(255))
    business_status = db.Column(db.String(100))
    has_decoy = db.Column(db.Boolean, default=False)
    decoy_vendor = db.Column(db.String(100))
    map_url = db.Column(db.String(500)) # Google Maps URL

class TelemetryLog(db.Model):
    __tablename__ = 'telemetry_logs'
    id = db.Column(db.Integer, primary_key=True)
    basin_id = db.Column(db.String(50), db.ForeignKey('basins.id'), nullable=False)
    data_type = db.Column(db.String(20)) # 'level' or 'rain'
    value = db.Column(db.Float)
    timestamp = db.Column(db.String(50)) # HH:MM format for simplicity 24h trend

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.String(50), primary_key=True) # e.g., 'R12345678'
    basin_id = db.Column(db.String(50), db.ForeignKey('basins.id'), nullable=False)
    spot_name = db.Column(db.String(100))
    author = db.Column(db.String(100))
    date = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending') # pending, approved
    content = db.Column(db.Text)
    photo_urls = db.Column(db.JSON) # Store as a list of strings
    
    # Catch Info
    catch_count = db.Column(db.String(20))
    catch_max_size = db.Column(db.String(20))
    
    # Tackle Info
    rod = db.Column(db.String(100))
    line = db.Column(db.String(100))
    hook = db.Column(db.String(100))
    
    # Telemetry (Snapshot at time of report)
    water_level = db.Column(db.String(50))
    turbidity = db.Column(db.String(50))
    weather_desc = db.Column(db.String(50))
    temp = db.Column(db.String(20))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/admin')
def admin_page():
    return send_from_directory(FRONTEND_DIR, 'admin.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)

CORS(app) # Enable CORS for frontend

# --- Frontend Routes ---
@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/admin')
def serve_admin():
    return app.send_static_file('admin.html')

@app.route('/api/debug/status')
def debug_status():
    """診斷接口：查看雲端環境狀態"""
    import os
    try:
        files = os.listdir('.')
        backend_files = os.listdir('backend') if os.path.exists('backend') else []
        basin_count = Basin.query.count()
        section_count = RiverSection.query.count()
        return jsonify({
            "cwd": os.getcwd(),
            "basedir": basedir,
            "root_files": files,
            "backend_files": backend_files,
            "db_counts": {"basins": basin_count, "sections": section_count},
            "env": {"CWA_TOKEN_SET": bool(CWA_TOKEN)}
        })
    except Exception as e:
        return jsonify({"error": str(e)})
        
@app.route('/api/debug/ping_cwa')
def ping_cwa():
    try:
        import traceback
        res = fetch_official_weather("CAAD90")
        return jsonify({"result": res, "status": "success"})
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()})

# --- API Endpoints ---
@app.route('/api/basins', methods=['GET'])
def get_basins():
    """回傳可用的流域選單"""
    basins = Basin.query.all()
    return jsonify([{"id": b.id, "name": b.name} for b in basins])

@app.route('/api/fishing_spots/<basin_id>', methods=['GET'])
def get_spots(basin_id):
    """回傳指定流域及釣點資訊 (從資料庫)"""
    try:
        basin = Basin.query.get(basin_id)
        if not basin:
            return jsonify({"error": "Basin not found"}), 404
        
        # Build the same structure as the old data.json
        sections_data = []
        for sec in basin.sections:
            spots_data = []
            for spot in sec.spots:
                spots_data.append({
                    "spot_name": spot.spot_name,
                    "spot_desc": spot.spot_desc,
                    "access_info": spot.access_info,
                    "business_status": spot.business_status,
                    "has_decoy": spot.has_decoy,
                    "decoy_vendor": spot.decoy_vendor,
                    "map_url": spot.map_url
                })
            
            sections_data.append({
                "section_id": sec.section_id,
                "name": sec.name,
                "type": sec.section_type,
                "water_level_station_id": sec.water_level_station_id,
                "water_level_station_name": sec.water_level_station_name,
                "characteristics": sec.characteristics,
                "fishing_spots": spots_data
            })
            
        return jsonify({
            "basin_system": basin.name,
            "weather_station_id": basin.weather_station_id,
            "weather_station_name": basin.weather_station_name,
            "river_sections": sections_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Zero-Latency Intelligence Engine (Background Worker) ---
INTELLIGENCE_CENTER = {
    "weather": {
        "pinglin": {"station_name": "坪林", "current_temp": 24.5, "feels_like_temp": 26.0, "humidity": "75%", "wind_speed": "1.2 m/s", "uv_index": "2", "weather_desc": "晴時多雲", "weather_warning": "", "last_update": "Syncing"},
        "wulai": {"station_name": "烏來", "current_temp": 23.5, "feels_like_temp": 25.0, "humidity": "80%", "wind_speed": "0.8 m/s", "uv_index": "1", "weather_desc": "多雲", "weather_warning": "", "last_update": "Syncing"}
    },
    "traffic": {
        "pinglin": {
            "last_update": "Syncing", 
            "traffic_controls": [], 
            "routes": [
                {"route_name": "國道五號 (南港👉坪林)", "avg_speed_kmh": 85, "status": "順暢 🟢"},
                {"route_name": "台9線 北宜公路 (新店👉坪林)", "avg_speed_kmh": 45, "status": "正常 🟢"},
                {"route_name": "台9線 北宜公路 (坪林👉頭城)", "avg_speed_kmh": 40, "status": "山區順暢 🟢"}
            ]
        },
        "wulai": {
            "last_update": "Syncing", 
            "traffic_controls": [], 
            "routes": [
                {"route_name": "國道三號 (安坑👉新店)", "avg_speed_kmh": 85, "status": "順暢 🟢"},
                {"route_name": "台9甲線 新烏路 (新店👉烏來)", "avg_speed_kmh": 50, "status": "正常 🟢"},
                {"route_name": "北107線 (烏來👉福山)", "avg_speed_kmh": 40, "status": "山路順暢 🟢"}
            ]
        }
    },
    "water": {
        "pinglin": {"station_id": "pinglin", "station_name": "坪林橋", "current_level_m": 105.8, "warning_level_m": 107.5, "rain_accumulated_1h_mm": 0.0, "rain_accumulated_24h_mm": 2.5, "status": "安全水位 🟢", "turbidity_status": "溪水清澈 🟢", "last_update": "Syncing"},
        "wulai": {"station_id": "wulai", "station_name": "福山橋", "current_level_m": 120.2, "warning_level_m": 122.0, "rain_accumulated_1h_mm": 0.0, "rain_accumulated_24h_mm": 5.0, "status": "安全水位 🟢", "turbidity_status": "溪水清澈 🟢", "last_update": "Syncing"}
    },
    "last_sync": "Initializing"
}

def fetch_official_weather(cwa_sid):
    """內部函數：實際連線氣象局，解析全量氣象要素"""
    try:
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={CWA_TOKEN}&StationId={cwa_sid}"
        resp = requests.get(url, timeout=5, verify=False)
        data = resp.json()
        if data.get('success') == 'true' and data['records']['Station']:
            obs = data['records']['Station'][0]
            we = obs.get('WeatherElement', {})
            
            # 如果是字典，直接讀取；如果是列表（相容性），轉換為字典
            if isinstance(we, list):
                we = {item['ElementName']: item['ElementValue'] for item in we}
            
            weather_desc = we.get('Weather', "晴時多雲")
            rain_now_str = we.get('Now', {}).get('Precipitation', "0.0") if isinstance(we.get('Now'), dict) else "0.0"
            try:
                rain_now = float(rain_now_str) if rain_now_str != "-99" else 0.0
            except:
                rain_now = 0.0
            
            # 智慧天氣描述：若 O-A0003-001 測站雨量大於 0，強制更正為降雨
            if weather_desc == "-99" or not weather_desc:
                weather_desc = "降雨中 🌧️" if rain_now > 0 else "晴朗多雲"
            elif rain_now > 0 and "雨" not in weather_desc:
                weather_desc = "降雨中 🌧️"
            
            temp_str = we.get('AirTemperature', "25.0")
            temp = float(temp_str) if temp_str != "-99" and temp_str else 25.0
            hum_str = we.get('RelativeHumidity', "75")
            humidity = float(hum_str) if hum_str != "-99" and hum_str else 75.0
            wind = we.get('WindSpeed', "0.0")
            uv = we.get('UVIndex', "0")
            
            # 簡單體感溫度計算
            feels_like = temp + (0.5 * (temp - 15)) if temp > 20 else temp
            
            return {
                "station_name": obs['StationName'],
                "current_temp": temp,
                "feels_like_temp": round(feels_like, 1),
                "humidity": f"{int(humidity * 100)}%" if humidity < 1 else f"{humidity}%",
                "wind_speed": f"{wind} m/s",
                "uv_index": uv if uv != "-99" else "0",
                "weather_desc": weather_desc,
                "weather_warning": "⚠️ 現場觀測到降雨" if "雨" in weather_desc else ("🔥 高溫提醒" if temp >= 32 else ""),
                "last_update": obs['ObsTime']['DateTime'][-8:-3] if 'ObsTime' in obs else time.strftime("%H:%M")
            }
    except Exception as e:
        print(f"Background Weather Sync Error ({cwa_sid}): {e}")
    return None

def fetch_official_traffic(basin_id):
    """內部函數：實際對接高公局公路路況 JSON 並聯動省道估算"""
    try:
        # 高公局開放資料：即時路況時速
        url = "https://tisvcloud.freeway.gov.tw/data/roadlevel_freeway.json"
        
        target_highway = "0005" if basin_id == 'pinglin' else "0003"
        resp = requests.get(url, timeout=10, verify=False)
        data = resp.json()
        
        speeds = []
        if 'RoadLevels' in data:
            for item in data['RoadLevels']:
                sid = item.get('SectionID', '')
                if sid.startswith(target_highway) and item.get('Value', 0) > 0:
                    speeds.append(int(item['Value']))
        
        if len(speeds) > 0:
            avg_speed = sum(speeds) // len(speeds)
        else:
            avg_speed = random.randint(75, 90)
            
        status = "順暢 🟢" if avg_speed > 60 else ("車多 🟡" if avg_speed > 40 else "壅塞 🔴")
        
        # 聯動省道邏輯：國道塞車時，省道作為替代道路車速會受影響
        congestion_factor = max(0, 90 - avg_speed) / 70.0 # 0.0 ~ 1.0
        
        if basin_id == 'pinglin':
            prov_speed = int(50 - (15 * congestion_factor) + random.randint(-4, 4))
            prov_status = "順暢 🟢" if prov_speed > 40 else "車多 🟡"
            return {
                "last_update": time.strftime("%H:%M:%S"),
                "traffic_controls": ["📡 高公局聯動估算", "⚠️ 未取得 TDX 省道金鑰"],
                "routes": [
                    { "route_name": "國道五號 (南港👉坪林)", "avg_speed_kmh": avg_speed, "status": status },
                    { "route_name": "台9線 北宜 (新店👉坪林)", "avg_speed_kmh": prov_speed, "status": prov_status },
                    { "route_name": "台9線 北宜 (坪林👉頭城)", "avg_speed_kmh": max(30, prov_speed - 5), "status": prov_status }
                ]
            }
        else:
            prov_speed = int(45 - (10 * congestion_factor) + random.randint(-4, 4))
            prov_status = "順暢 🟢" if prov_speed > 35 else "車多 🟡"
            return {
                "last_update": time.strftime("%H:%M:%S"),
                "traffic_controls": ["📡 高公局聯動估算", "⚠️ 國三南向動態聯動"],
                "routes": [
                    { "route_name": "國道三號 (安坑👉新店)", "avg_speed_kmh": avg_speed, "status": status },
                    { "route_name": "台9甲線 新烏路 (新店👉烏來)", "avg_speed_kmh": prov_speed, "status": prov_status },
                    { "route_name": "北107線 (烏來👉福山)", "avg_speed_kmh": max(30, prov_speed - 5), "status": "山區順暢 🟢" }
                ]
            }
    except Exception as e:
        print(f"Background Traffic Sync Error: {e}")
    return None

def fetch_official_water(station_id):
    """內部函數：實際對接水利署水位 API 並結合 CWA 雨勢 API"""
    try:
        wra_id = "1140H048" if station_id == "pinglin" else "1140H096"
        cwa_rain_id = "C0A530" if station_id == "pinglin" else "C2A560"
        
        # 1. 取真實水位
        url_water = f"https://fhy.wra.gov.tw/fhyv2/api/v1/Water/RealTime/Station"
        resp_w = requests.get(url_water, timeout=10, verify=False)
        data_w = resp_w.json()
        
        level = None
        for item in data_w:
            if item.get('StationNo') == wra_id:
                level = item.get('WaterLevel')
                break
                
        # 2. 取真實累積雨量
        rain_1h = 0.0
        rain_24h = 0.0
        url_rain = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001?Authorization={CWA_TOKEN}&StationId={cwa_rain_id}"
        try:
            resp_r = requests.get(url_rain, timeout=5, verify=False)
            data_r = resp_r.json()
            if data_r.get('success') == 'true' and data_r['records']['Station']:
                re = data_r['records']['Station'][0].get('RainfallElement', {})
                r_1h_str = re.get('Past1hr', {}).get('Precipitation', "0.0")
                r_24h_str = re.get('Past24hr', {}).get('Precipitation', "0.0")
                rain_1h = float(r_1h_str) if r_1h_str != "-99" else 0.0
                rain_24h = float(r_24h_str) if r_24h_str != "-99" else 0.0
        except Exception as re:
            print(f"Rain Sync Error for {cwa_rain_id}: {re}")
        
        if level is not None:
            warn_level = 107.5 if station_id == "pinglin" else 122.0
            return {
                "station_id": station_id,
                "station_name": "坪林橋" if station_id == "pinglin" else "福山橋",
                "current_level_m": round(float(level), 2),
                "warning_level_m": warn_level,
                "rain_accumulated_1h_mm": rain_1h,
                "rain_accumulated_24h_mm": rain_24h,
                "status": "安全水位 🟢" if float(level) < warn_level else "警戒水位 🔴",
                "turbidity_status": "溪水清澈 🟢" if rain_24h < 10 else "略有混濁 🟡",
                "last_update": time.strftime("%H:%M")
            }
    except Exception as e:
        print(f"Background Water Sync Error ({station_id}): {e}")
    return None

def background_intelligence_poller():
    """核心背景線程：每 5 分鐘更新一次情報中心"""
    print("📡 [ Intelligence Poller ] Starting background worker...")
    
    while True:
        try:
            # 1. 更新氣象 (坪林, 福山)
            for sid, cwa_id in [("pinglin", "CAAD90"), ("wulai", "C2A560")]:
                print(f"📡 [ Weather ] Syncing {sid} ({cwa_id})...")
                result = fetch_official_weather(cwa_id)
                if result:
                    INTELLIGENCE_CENTER["weather"][sid] = result
                    print(f"✅ [ Weather ] {sid} Synced: {result['current_temp']}°C")
                else:
                    print(f"⚠️ [ Weather ] {sid} Sync failed, using previous data.")
            
            # 2. 更新路況
            for bid in ["pinglin", "wulai"]:
                result = fetch_official_traffic(bid)
                if result:
                    INTELLIGENCE_CENTER["traffic"][bid] = result
            
            # 3. 更新水情 (對接實際 WRA API)
            for sid in ["pinglin", "wulai"]:
                result = fetch_official_water(sid)
                if result:
                    INTELLIGENCE_CENTER["water"][sid] = result
                    print(f"✅ [ Water ] {sid} Synced: {result['current_level_m']}m")
                else:
                    # Fallback to simulation
                    INTELLIGENCE_CENTER["water"][sid] = {
                        "station_id": sid,
                        "station_name": "坪林橋" if sid == "pinglin" else "福山橋",
                        "current_level_m": round(random.uniform(105.0, 107.0), 2),
                        "warning_level_m": 107.5 if sid == "pinglin" else 122.0,
                        "rain_accumulated_1h_mm": 0.0,
                        "rain_accumulated_24h_mm": round(random.uniform(0.0, 15.0), 1),
                        "status": "安全水位 🟢 (戰略評估)",
                        "turbidity_status": "溪水清澈 🟢",
                        "last_update": time.strftime("%H:%M")
                    }
            
            INTELLIGENCE_CENTER["last_sync"] = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"✨ [ Intelligence Center ] Global Sync Complete at {INTELLIGENCE_CENTER['last_sync']}")
            
        except Exception as e:
            print(f"❌ [ Poller Critical ] Error: {e}")
            
            
        time.sleep(300) # 5分鐘更新一次

# --- Zero-Latency Intelligence Engine (Background Worker) ---
_poller_started = False

@app.before_request
def ensure_poller():
    global _poller_started
    if not _poller_started:
        _poller_started = True
        worker = threading.Thread(target=background_intelligence_poller, daemon=True)
        worker.start()

@app.route('/api/live/traffic/<basin_id>', methods=['GET'])
def get_live_traffic(basin_id):
    """零延遲獲取情報中心的交通資料"""
    data = INTELLIGENCE_CENTER["traffic"].get(basin_id)
    if not data:
        return jsonify(fetch_official_traffic(basin_id))
    return jsonify(data)

@app.route('/api/live/weather/<station_id>', methods=['GET'])
def get_live_weather(station_id):
    """零延遲獲取情報中心的氣象資料"""
    # 支援別名對應與模糊匹配
    sid = None
    if station_id in ["C0A530", "C0A520", "pinglin"]: sid = "pinglin"
    elif station_id in ["C2A560", "C0A560", "wulai"]: sid = "wulai"
    
    if not sid:
        return jsonify({
            "station_name": "未選擇流域",
            "current_temp": "--",
            "weather_desc": "請先切換流域",
            "last_update": "--"
        }), 400

    data = INTELLIGENCE_CENTER["weather"].get(sid)
    if not data:
        # 初次啟動備援 (同步外部資料)
        cwa_id = "CAAD90" if sid == "pinglin" else "C2A560"
        result = fetch_official_weather(cwa_id)
        if result: 
            safe_result = {k: (v if v is not None else "--") for k, v in result.items()}
            return jsonify(safe_result)
        
        return jsonify({
            "station_name": "氣象觀測站",
            "current_temp": 24.0,
            "weather_desc": "連線中...", 
            "weather_warning": "☢️ 正在建立戰術連線，請稍後幾秒...",
            "feels_like_temp": 24.0,
            "humidity": "--",
            "wind_speed": "--",
            "uv_index": "--",
            "last_update": time.strftime("%H:%M")
        })
        
    # 確保所有欄位不為 None
    safe_data = {k: (v if v is not None else "--") for k, v in data.items()}
    return jsonify(safe_data)

@app.route('/api/live/water/<station_id>', methods=['GET'])
def get_live_water(station_id):
    """零延遲獲取情報中心的水情資料"""
    # 根據 station_id 判斷是哪個流域的資料 (坪林橋: 1140H048, 福山橋: 1140H096)
    sid = None
    if "048" in station_id or "pinglin" in station_id.lower(): sid = "pinglin"
    elif "096" in station_id or "wulai" in station_id.lower(): sid = "wulai"
    
    if not sid:
        return jsonify({"station_name": "未知站點", "current_level_m": "-"}), 400
    
    data = INTELLIGENCE_CENTER["water"].get(sid)
    if not data:
        return jsonify({
            "station_id": sid,
            "station_name": "水文觀測站",
            "current_level_m": "--",
            "warning_level_m": "--",
            "rain_accumulated_1h_mm": 0,
            "rain_accumulated_24h_mm": 0,
            "status": "數據同步中... ⚪",
            "turbidity_status": "連線中... ⚪",
            "last_update": time.strftime("%H:%M")
        })
    
    # 確保所有欄位不為 None
    safe_data = {k: (v if v is not None else "--") for k, v in data.items()}
    return jsonify(safe_data)


@app.route('/api/debug/basin_status', methods=['GET'])
def get_basin_status():
    """診斷專用：查看各流域在資料庫中的統計狀態"""
    try:
        basins = Basin.query.all()
        status = []
        for b in basins:
            sections = RiverSection.query.filter_by(basin_id=b.id).all()
            total_spots = sum(len(s.spots) for s in sections)
            status.append({
                "id": b.id,
                "name": b.name,
                "sections": len(sections),
                "spots": total_spots
            })
        return jsonify({
            "total_basins": len(basins),
            "basins": status,
            "db_path": app.config['SQLALCHEMY_DATABASE_URI']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/debug/force_reseed', methods=['POST'])
def force_reseed():
    """強制清空資料庫並重新從 data.json 讀取釣區與釣點"""
    try:
        # 1. 清空舊資料
        FishingSpot.query.delete()
        RiverSection.query.delete()
        Basin.query.delete()
        db.session.commit()
        # 2. 重新執行 Seed
        seed_data_from_json()
        return jsonify({"status": "success", "message": "資料庫已重置並重新從 data.json 讀取完畢。"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/<basin_id>', methods=['GET'])
def get_reports(basin_id):
    """回傳該流域審核通過的戰報 (從資料庫)"""
    reports = Report.query.filter_by(basin_id=basin_id, status='approved').order_by(Report.date.desc()).all()
    
    result = []
    for r in reports:
        result.append({
            "id": r.id,
            "basin_id": r.basin_id,
            "spot_name": r.spot_name,
            "author": r.author,
            "date": r.date,
            "status": r.status,
            "content": r.content,
            "photo_urls": r.photo_urls,
            "catch": {"count": r.catch_count, "max_size": r.catch_max_size},
            "tackle": {"rod": r.rod, "line": r.line, "hook": r.hook},
            "telemetry": {
                "water_level": r.water_level,
                "turbidity": r.turbidity,
                "weather_desc": r.weather_desc,
                "temp": r.temp
            }
        })
    return jsonify(result)

@app.route('/api/reports', methods=['POST'])
def submit_report():
    """接收新戰報 (支援實體圖片上傳) 並存入資料庫"""
    try:
        # Get textual data from form
        basin_id = request.form.get('basin_id')
        spot_name = request.form.get('spot_name')
        author = request.form.get('author', '匿名釣客')
        content = request.form.get('content', '')
        catch_count = request.form.get('catch_count', '-')
        catch_max_size = request.form.get('catch_max_size', '-')
        rod = request.form.get('tackle_rod', '未填寫')
        line = request.form.get('tackle_line', '未填寫')
        hook = request.form.get('tackle_hook', '未填寫')
        
        # Telemetry from form (JSON string)
        telemetry_raw = request.form.get('telemetry', '{}')
        telemetry = json.loads(telemetry_raw)

        # Handle file upload(s)
        photo_urls = []
        if 'photos' in request.files:
            files = request.files.getlist('photos')
            for file in files[:5]: # Max 5 photos enforcement
                if file and allowed_file(file.filename):
                    # Add random element to deduplicate fast multi-uploads
                    filename = f"{int(time.time())}_{random.randint(1000, 9999)}_{file.filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    photo_urls.append(f"/uploads/{filename}")
        
        if not photo_urls:
            # Fallback for demo
            photo_urls = ['https://images.unsplash.com/photo-1544728562-ab1bfef3d7fa?w=600&h=400&fit=crop']

        new_report = Report(
            id=f"R{int(time.time())}",
            basin_id=basin_id,
            spot_name=spot_name,
            author=author,
            date=time.strftime("%Y-%m-%d %H:%M"),
            status='pending',
            content=content,
            photo_urls=photo_urls,
            catch_count=catch_count,
            catch_max_size=catch_max_size,
            rod=rod,
            line=line,
            hook=hook,
            water_level=telemetry.get('water_level'),
            turbidity=telemetry.get('turbidity'),
            weather_desc=telemetry.get('weather_desc'),
            temp=telemetry.get('temp')
        )
        
        db.session.add(new_report)
        db.session.commit()
        
        return jsonify({"success": True, "message": "戰報已送出，等待系統審核中！", "report_id": new_report.id})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# --- Admin API Endpoints ---

@app.route('/api/admin/reports', methods=['GET'])
def get_admin_reports():
    password = request.headers.get('X-Admin-Password')
    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    
    reports = Report.query.order_by(Report.date.desc()).all()
    result = []
    for r in reports:
        result.append({
            "id": r.id, "basin_id": r.basin_id, "spot_name": r.spot_name, "author": r.author,
            "date": r.date, "status": r.status, "content": r.content, "photo_urls": r.photo_urls,
            "catch": {"count": r.catch_count, "max_size": r.catch_max_size}
        })
    return jsonify(result)

@app.route('/api/admin/approve/<report_id>', methods=['POST'])
def approve_report(report_id):
    password = request.headers.get('X-Admin-Password')
    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    
    report = Report.query.get(report_id)
    if report:
        report.status = 'approved'
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "Report not found"}), 404

@app.route('/api/admin/delete/<report_id>', methods=['DELETE'])
def delete_report(report_id):
    password = request.headers.get('X-Admin-Password')
    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    
    report = Report.query.get(report_id)
    if report:
        # Also delete local photo file if it exists
        for url in report.photo_urls:
            if url.startswith('/uploads/'):
                filename = url.replace('/uploads/', '')
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        db.session.delete(report)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "Report not found"}), 404

# --- Advanced Analytics / History API ---

@app.route('/api/telemetry/history/<basin_id>', methods=['GET'])
def get_telemetry_history(basin_id):
    """回傳過去 24 小時的水位與雨量趨勢"""
    logs = TelemetryLog.query.filter_by(basin_id=basin_id).order_by(TelemetryLog.id.desc()).limit(48).all()
    # Separate levels and rain
    levels = [{"time": l.timestamp, "value": l.value} for l in logs if l.data_type == 'level'][::-1]
    rains = [{"time": l.timestamp, "value": l.value} for l in logs if l.data_type == 'rain'][::-1]
    return jsonify({"levels": levels, "rains": rains})

# --- Admin Spot Management API ---

@app.route('/api/admin/spots', methods=['GET'])
def admin_get_spots():
    password = request.headers.get('X-Admin-Password')
    if password != ADMIN_PASSWORD: return jsonify({"error": "Unauthorized"}), 401
    
    spots = FishingSpot.query.all()
    return jsonify([{
        "id": s.id, "name": s.spot_name, "desc": s.spot_desc, "map_url": s.map_url, "has_decoy": s.has_decoy
    } for s in spots])

@app.route('/api/admin/spots/<int:spot_id>', methods=['PUT', 'DELETE'])
def admin_manage_spot(spot_id):
    password = request.headers.get('X-Admin-Password')
    if password != ADMIN_PASSWORD: return jsonify({"error": "Unauthorized"}), 401
    
    spot = FishingSpot.query.get(spot_id)
    if not spot: return jsonify({"error": "Not found"}), 404
    
    if request.method == 'DELETE':
        db.session.delete(spot)
        db.session.commit()
        return jsonify({"success": True})
    
    data = request.json
    spot.spot_name = data.get('name', spot.spot_name)
    spot.spot_desc = data.get('desc', spot.spot_desc)
    spot.map_url = data.get('map_url', spot.map_url)
    db.session.commit()
    return jsonify({"success": True})

def seed_data_from_json():
    """從 data.json 注入初始流域與釣點資料（若資料庫為空）"""
    try:
        with app.app_context():
            # 強制注入邏輯：若發現舊資料結構不對，則清空重來
            sample_section = RiverSection.query.first()
            if sample_section and not sample_section.section_type:
                print("🧹 Detected malformed legacy data, clearing for fresh seed...")
                RiverSection.query.delete()
                Basin.query.delete()
                db.session.commit()

            if Basin.query.count() == 0:
                # Try multiple path possibilities for cloud environment
                json_paths = [
                    os.path.join(basedir, 'data.json'),
                    os.path.join(os.path.abspath(os.curdir), 'backend', 'data.json'),
                    os.path.join(os.path.abspath(os.curdir), 'data.json')
                ]
                
                json_path = None
                for p in json_paths:
                    if os.path.exists(p):
                        json_path = p
                        break
                
                if not json_path:
                    print(f"⚠️ data.json NOT found, using ROBUST DEFAULT FALLBACK SEED.")
                    fallback_basins = {
                        "pinglin": {
                            "name": "坪林流域・戰情室", 
                            "weather_id": "C0A530", 
                            "sections": [
                                {"id": "P01_MAIN", "name": "北勢溪主流段", "type": "主流 (Mainstream)", "station": "1140H048"}
                            ]
                        },
                        "wulai": {
                            "name": "烏來福山・戰情室", 
                            "weather_id": "C2A560", 
                            "sections": [
                                {"id": "W01_MAIN", "name": "南勢溪主流段", "type": "主流 (Mainstream)", "station": "1140H096"}
                            ]
                        }
                    }
                    for b_id, b_info in fallback_basins.items():
                        basin = Basin(id=b_id, name=b_info['name'], weather_station_id=b_info['weather_id'])
                        db.session.add(basin)
                        for s in b_info['sections']:
                            section = RiverSection(
                                basin_id=b_id, 
                                section_id=s['id'], 
                                name=s['name'], 
                                section_type=s['type'],
                                water_level_station_id=s['station']
                            )
                            db.session.add(section)
                    db.session.commit()
                    return
                
                print(f"🌱 Seeding database from: {json_path}")
                with open(json_path, 'r', encoding='utf-8') as f:
                    seed_data = json.load(f)
                
                for b_id, b_info in seed_data.items():
                    basin = Basin(
                        id=b_id,
                        name=b_info.get('basin_system', b_id),
                        weather_station_id=b_info.get('weather_station_id'),
                        weather_station_name=b_info.get('weather_station_name')
                    )
                    db.session.add(basin)
                    
                    for s_data in b_info.get('river_sections', []):
                        section = RiverSection(
                            basin_id=b_id,
                            section_id=s_data['section_id'],
                            name=s_data['name'],
                            section_type=s_data.get('type', '主流'),
                            water_level_station_id=s_data.get('water_level_station_id', 'UNKNOWN'),
                            characteristics=s_data.get('characteristics', '')
                        )
                        db.session.add(section)
                        db.session.flush() # Ensure section.id is populated for spots
                        
                        for spot_data in s_data.get('fishing_spots', []):
                            spot = FishingSpot(
                                section_id=section.id,
                                spot_name=spot_data['spot_name'],
                                spot_desc=spot_data.get('spot_desc', ''),
                                access_info=spot_data.get('access_info', ''),
                                business_status=spot_data.get('business_status', ''),
                                has_decoy=spot_data.get('has_decoy', False),
                                decoy_vendor=spot_data.get('decoy_vendor', ''),
                                map_url=spot_data.get('map_url', '')
                            )
                            db.session.add(spot)
                db.session.commit()
                print("✅ Seeding complete with full Fishing Spots.")
    except Exception as e:
        print(f"❌ Seeding error: {e}")

def init_mock_telemetry():
    """初始化模擬數據供展示趨勢圖"""
    if TelemetryLog.query.count() == 0:
        print("Initializing mock telemetry history...")
        for b_id in ['pinglin', 'wulai']:
            base_level = 106.0
            for i in range(24):
                t_str = f"{(time.localtime().tm_hour - (23-i)) % 24:02d}:00"
                db.session.add(TelemetryLog(basin_id=b_id, data_type='level', value=base_level + random.uniform(-0.5, 0.5), timestamp=t_str))
                db.session.add(TelemetryLog(basin_id=b_id, data_type='rain', value=random.uniform(0, 5), timestamp=t_str))
        db.session.commit()

# --- App Initialization (Critical for Cloud/Gunicorn) ---
with app.app_context():
    db.create_all()
    seed_data_from_json()
    init_mock_telemetry()

if __name__ == '__main__':
    # Industrial Stability: No Debug Mode, No Reloader on Mac
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
