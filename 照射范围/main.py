# -*- coding: utf-8 -*-
# Globe-Trader-Sync v1.5 (Production Release)
# 首席架构师交付 - 无感内存代理 + 真实 API 抓取

import http.server
import socketserver
import threading
import webbrowser
import json
import time
import os
import re
import requests
from datetime import datetime, timedelta

# ==========================================
# 1. 业务核心配置与状态 (Business Context)
# ==========================================
PROXIES = {}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
CITY_DB_FILE = "city_db.json"

# 别名词典：用于拦截 Polymarket 的奇葩缩写
ALIAS_MAP = {
    "NYC": "New York", "DC": "Washington", "LA": "Los Angeles", "DFW": "Dallas"
}

DEFAULT_DB = {
    "Atlanta": {"name": "亚特兰大", "lat": 33.6407, "lon": -84.4277, "tz": "America/New_York", "slug": "atlanta"},
    "Lucknow": {"name": "勒克瑙", "lat": 26.7606, "lon": 80.8893, "tz": "Asia/Kolkata", "slug": "lucknow"},
    "Chicago": {"name": "芝加哥", "lat": 41.9742, "lon": -87.9073, "tz": "America/Chicago", "slug": "chicago"},
    "Warsaw": {"name": "华沙", "lat": 52.1640, "lon": 20.9700, "tz": "Europe/Warsaw", "slug": "warsaw"},
    "London": {"name": "伦敦", "lat": 51.4700, "lon": -0.4543, "tz": "Europe/London", "slug": "london"},
    "Wellington": {"name": "惠灵顿", "lat": -41.3291, "lon": 174.8071, "tz": "Pacific/Auckland", "slug": "wellington"},
    "Shanghai": {"name": "上海", "lat": 31.1443, "lon": 121.8083, "tz": "Asia/Shanghai", "slug": "shanghai"},
    "Seoul": {"name": "首尔", "lat": 37.4602, "lon": 126.4407, "tz": "Asia/Seoul", "slug": "seoul"},
    "Singapore": {"name": "新加坡", "lat": 1.3644, "lon": 103.9915, "tz": "Asia/Singapore", "slug": "singapore"},
    "Miami": {"name": "迈阿密", "lat": 25.7959, "lon": -80.2870, "tz": "America/New_York", "slug": "miami"},
    "Paris": {"name": "巴黎", "lat": 49.0097, "lon": 2.5479, "tz": "Europe/Paris", "slug": "paris"},
    "New York": {"name": "纽约", "lat": 40.7812, "lon": -73.9665, "tz": "America/New_York", "slug": "new-york"},
    "Tokyo": {"name": "东京", "lat": 35.5494, "lon": 139.7798, "tz": "Asia/Tokyo", "slug": "tokyo"},
    "Ankara": {"name": "安卡拉", "lat": 40.1281, "lon": 32.9951, "tz": "Europe/Istanbul", "slug": "ankara"},
    "Shenzhen": {"name": "深圳", "lat": 22.6393, "lon": 113.8107, "tz": "Asia/Shanghai", "slug": "shenzhen"},
    "Buenos Aires": {"name": "布宜诺斯艾利斯", "lat": -34.8150, "lon": -58.5348, "tz": "America/Argentina/Buenos_Aires", "slug": "buenos-aires"},
    "Chongqing": {"name": "重庆", "lat": 29.7192, "lon": 106.6417, "tz": "Asia/Shanghai", "slug": "chongqing"},
    "Toronto": {"name": "多伦多", "lat": 43.6777, "lon": -79.6248, "tz": "America/Toronto", "slug": "toronto"},
    "Beijing": {"name": "北京", "lat": 39.8000, "lon": 116.4700, "tz": "Asia/Shanghai", "slug": "beijing"},
    "Hong Kong": {"name": "香港", "lat": 22.3020, "lon": 114.1740, "tz": "Asia/Hong_Kong", "slug": "hong-kong"},
    "Seattle": {"name": "西雅图", "lat": 47.4502, "lon": -122.3088, "tz": "America/Los_Angeles", "slug": "seattle"},
    "Wuhan": {"name": "武汉", "lat": 30.7761, "lon": 114.2081, "tz": "Asia/Shanghai", "slug": "wuhan"},
    "Denver": {"name": "丹佛", "lat": 39.8561, "lon": -104.6737, "tz": "America/Denver", "slug": "denver"},
    "Madrid": {"name": "马德里", "lat": 40.4983, "lon": -3.5676, "tz": "Europe/Madrid", "slug": "madrid"},
    "Dallas": {"name": "达拉斯", "lat": 32.8998, "lon": -97.0403, "tz": "America/Chicago", "slug": "dallas"},
    "Chengdu": {"name": "成都", "lat": 30.5785, "lon": 103.9471, "tz": "Asia/Shanghai", "slug": "chengdu"},
    "Los Angeles": {"name": "洛杉矶", "lat": 33.9416, "lon": -118.4085, "tz": "America/Los_Angeles", "slug": "los-angeles"},
    "Sao Paulo": {"name": "圣保罗", "lat": -23.4356, "lon": -46.4731, "tz": "America/Sao_Paulo", "slug": "sao-paulo"},
    "Milan": {"name": "米兰", "lat": 45.6301, "lon": 8.7255, "tz": "Europe/Rome", "slug": "milan"},
    "Munich": {"name": "慕尼黑", "lat": 48.3537, "lon": 11.7750, "tz": "Europe/Berlin", "slug": "munich"},
    "Taipei": {"name": "台北", "lat": 25.0797, "lon": 121.2342, "tz": "Asia/Taipei", "slug": "taipei"},
    "Tel Aviv": {"name": "特拉维夫", "lat": 32.0055, "lon": 34.8854, "tz": "Asia/Jerusalem", "slug": "tel-aviv"},
    "San Francisco": {"name": "旧金山", "lat": 37.6213, "lon": -122.3790, "tz": "America/Los_Angeles", "slug": "san-francisco"},
    "Austin": {"name": "奥斯汀", "lat": 30.1975, "lon": -97.6664, "tz": "America/Chicago", "slug": "austin"},
    "Houston": {"name": "休斯顿", "lat": 29.9902, "lon": -95.3368, "tz": "America/Chicago", "slug": "houston"},
    "Istanbul": {"name": "伊斯坦布尔", "lat": 41.0082, "lon": 28.9784, "tz": "Europe/Istanbul", "slug": "istanbul"}
}

# 全局内存仓库，替代 today_markets.json 落地文件
GLOBAL_MEMORY_DATA = {
    "status": "loading",
    "last_update": "",
    "payload": {}
}

# ==========================================
# 2. 核心抓取逻辑 (Data Pipeline)
# ==========================================
def get_utc8_time_anchors():
    utc_now = datetime.utcnow()
    utc8_now = utc_now + timedelta(hours=8)
    utc8_yesterday = utc8_now - timedelta(days=1)
    month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    today_title_str = f"on {month_names[utc8_now.month - 1]} {utc8_now.day}"
    yesterday_slug_date = f"{month_names[utc8_yesterday.month - 1].lower()}-{utc8_yesterday.day}-{utc8_yesterday.year}"
    return today_title_str, yesterday_slug_date

def normalize_temperature(text):
    if not text or text == "--": return "--°C"
    numbers = re.findall(r'\d+(?:\.\d+)?', text)
    if not numbers: return text
    max_val = max(float(n) for n in numbers)
    if "F" in text.upper(): max_val = (max_val - 32) * 5.0 / 9.0
    result_str = f"{max_val:.1f}°C"
    if "or higher" in text.lower(): return "↑" + result_str
    elif "or below" in text.lower(): return "↓" + result_str
    return result_str

def load_city_db():
    db = DEFAULT_DB.copy()
    if os.path.exists(CITY_DB_FILE):
        try:
            with open(CITY_DB_FILE, "r", encoding="utf-8") as f:
                db.update(json.load(f))
        except Exception:
            pass
    return db

def save_city_db(db):
    extensions = {k: v for k, v in db.items() if k not in DEFAULT_DB}
    if extensions:
        with open(CITY_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(extensions, f, ensure_ascii=False, indent=2)

def geocode_new_city(city_en):
    print(f"  [📡 卫星定位] 发现新城市 '{city_en}'，启动汉化引擎...")
    zh_headers = {"User-Agent": "WeatherGlobe-DataPipeline/4.0", "Accept-Language": "zh-CN,zh;q=0.9"}
    try:
        nom_url = f"https://nominatim.openstreetmap.org/search?q={city_en}&format=json&limit=1&accept-language=zh-CN"
        res = requests.get(nom_url, headers=zh_headers, timeout=5).json()
        if not res: return None
        zh_name = res[0].get('name', city_en)
        lat, lon = float(res[0]['lat']), float(res[0]['lon'])
        tz_url = f"https://timeapi.io/api/TimeZone/coordinate?latitude={lat}&longitude={lon}"
        tz = requests.get(tz_url, headers=zh_headers, timeout=5).json().get('timeZone', 'UTC')
        discovered_at = datetime.now().isoformat()
        return {"name": zh_name, "lat": lat, "lon": lon, "tz": tz, "discovered_at": discovered_at}
    except Exception:
        return None

def fetch_yesterday_precise(city_slug, yesterday_slug_date):
    slug = f"highest-temperature-in-{city_slug}-on-{yesterday_slug_date}"
    url = f"https://gamma-api.polymarket.com/events?slug={slug}"
    try:
        res = requests.get(url, headers=HEADERS, proxies=PROXIES, timeout=10)
        if res.status_code == 200 and len(res.json()) > 0:
            markets = res.json()[0].get("markets", [])
            winner_title, max_prob = "--", -1.0
            for m in markets:
                title = m.get("groupItemTitle", m.get("question", ""))
                resolution = str(m.get("resolution", "")).lower()
                temp_match = re.search(r"be (.*?) on", title)
                clean_title = temp_match.group(1) if temp_match else title

                if m.get("winner") is True or resolution in ["yes", "1", "true"]:
                    return normalize_temperature(clean_title)

                raw_prices = m.get("outcomePrices")
                if raw_prices:
                    try:
                        prices = json.loads(raw_prices) if isinstance(raw_prices, str) else raw_prices
                        if prices and float(prices[0]) > max_prob:
                            max_prob = float(prices[0])
                            winner_title = clean_title
                    except:
                        pass
            if winner_title != "--": return normalize_temperature(winner_title)
    except:
        pass
    return "等待链上结算"

def background_fetch_task():
    global GLOBAL_MEMORY_DATA
    city_db = load_city_db()
    today_title_str, yesterday_slug_date = get_utc8_time_anchors()
    
    print(f"\n--- [START] API 数据同步: {today_title_str} ---")
    url = "https://gamma-api.polymarket.com/events/pagination"
    all_events = []
    offset = 0
    limit = 100
    
    try:
        while True:
            params = {"limit": str(limit), "offset": str(offset), "active": "true", "tag_slug": "weather", "closed": "false"}
            response = requests.get(url, params=params, headers=HEADERS, proxies=PROXIES, timeout=15)
            data = response.json().get('data', [])
            if not data: break
            all_events.extend(data)
            if len(data) < limit: break
            offset += limit
            
        print(f"📡 深度探测完成：拉取 {len(all_events)} 个节点。开始处理...\n")

        output_data = {}
        db_updated = False

        for event in all_events:
            title = event.get('title', '')
            if today_title_str not in title: continue

            city_match = re.search(r"Highest temperature in (.*?) on", title)
            if not city_match: continue

            raw_city_en = city_match.group(1).strip()
            city_en = ALIAS_MAP.get(raw_city_en.upper(), raw_city_en)
            
            slug_match = re.search(r"highest-temperature-in-(.*?)-on", event.get('slug', ''))
            actual_city_slug = slug_match.group(1) if slug_match else city_en.lower().replace(" ", "-")

            highest_prob = -1.0
            predicted_temp_str = "--"

            for m in event.get('markets', []):
                p_str = m.get('outcomePrices', '[]')
                prices = json.loads(p_str) if isinstance(p_str, str) else p_str
                if prices:
                    prob = float(prices[0])
                    if prob > highest_prob:
                        highest_prob = prob
                        q_text = m.get('question', '')
                        temp_match = re.search(r"be (.*?) on", q_text)
                        predicted_temp_str = temp_match.group(1) if temp_match else q_text

            if city_en not in city_db:
                new_city_data = geocode_new_city(city_en)
                if new_city_data:
                    city_db[city_en] = new_city_data
                    db_updated = True
                else: continue

            db_info = city_db[city_en]
            
            is_new = False
            if city_en not in DEFAULT_DB:
                if "discovered_at" not in db_info:
                    db_info["discovered_at"] = datetime.now().isoformat()
                    db_updated = True
                    is_new = True
                else:
                    disc_time = datetime.fromisoformat(db_info["discovered_at"])
                    if datetime.now() - disc_time <= timedelta(days=3):
                        is_new = True
            
            print(f"   解析进度: {db_info['name']} ...", end="\r")
            y_temp = fetch_yesterday_precise(actual_city_slug, yesterday_slug_date)
            
            output_data[actual_city_slug] = {
                "name": db_info['name'],
                "lat": db_info['lat'],
                "lon": db_info['lon'],
                "tz": db_info['tz'],
                "is_new": is_new, 
                "yesterday_settled": y_temp,
                "today_predicted": normalize_temperature(predicted_temp_str),
                "confidence": f"{highest_prob * 100:.1f}%",
                "url": f"https://polymarket.com/zh/event/{event.get('slug', '')}"
            }

        if db_updated: save_city_db(city_db)

        # 🚨 不再写入文件，而是更新到内存变量供前端 API 读取
        GLOBAL_MEMORY_DATA = {
            "status": "success",
            "last_update": time.strftime("%Y-%m-%d %H:%M:%S"),
            "payload": output_data
        }
        print(f"\n✅ 数据载入内存！(捕获: {len(output_data)} 城市) - 前端自动刷新中...")

    except Exception as e:
        GLOBAL_MEMORY_DATA["status"] = "error"
        print(f"\n❌ 后台抓取线程崩溃: {e}")

# ==========================================
# 3. 本地服务与内存代理 (In-Memory Proxy)
# ==========================================
class FastTradeHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 拦截前端 API 请求，从内存读取数据并返回
        if self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(GLOBAL_MEMORY_DATA, ensure_ascii=False).encode('utf-8'))
        else:
            # 处理其他所有请求为静态文件请求 (index.html 等)
            super().do_GET()

    def log_message(self, format, *args):
        pass # 屏蔽 HTTP 日志，保持终端清洁

def run_production_server():
    # 锁定运行目录，保障分发安全性
    base_dir = os.path.dirname(os.path.abspath(__file__))
    web_dir = os.path.join(base_dir, '照射范围')
    os.chdir(web_dir if os.path.exists(web_dir) else base_dir)

    # 在后台独立线程中触发拉取，避免阻塞 HTTP 服务启动
    fetch_thread = threading.Thread(target=background_fetch_task)
    fetch_thread.daemon = True
    fetch_thread.start()

    # 智能寻找可用端口
    port = 8000
    httpd = None
    while port <= 8080:
        try:
            socketserver.TCPServer.allow_reuse_address = True
            httpd = socketserver.TCPServer(("", port), FastTradeHandler)
            break
        except OSError:
            port += 1
            
    if not httpd: return

    url = f"http://127.0.0.1:{port}/index.html"
    print(f"\n🌍 气象交易哨所 服务已启动 (端口 {port})")
    print(f"🚀 将自动打开浏览器...\n")
    
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 停止服务...")
        httpd.shutdown()

if __name__ == "__main__":
    run_production_server()
