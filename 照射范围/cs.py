import requests
import json
import re

# 代理配置 (确保 Clash 正在运行)
PROXIES = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 城市名称到 Polymarket Slug 的映射
CITY_MAP = {
    "首尔": "seoul",
    "东京": "tokyo",
    "上海": "shanghai",
    "武汉": "wuhan",
    "台湾": "taipei",      # Polymarket 标的通常为 Taipei
    "重庆": "chongqing",
    "成都": "chengdu",
    "印度": "lucknow",     # Polymarket 标的通常为 Lucknow
    "安卡拉": "ankara",
    "特拉维夫": "tel-aviv",
    "米兰": "milan",
    "慕尼黑": "munich",
    "华沙": "warsaw",
    "巴黎": "paris",
    "马德里": "madrid",
    "伦敦": "london"
}

DATES = ["march-27-2026", "march-28-2026"]

def normalize_temperature(text):
    if not text or text == "--": return "--"
    numbers = re.findall(r'\d+(?:\.\d+)?', text)
    if not numbers: return text
    max_val = max(float(n) for n in numbers)
    if "F" in text.upper(): max_val = (max_val - 32) * 5.0 / 9.0
    result_str = f"{max_val:.1f}°C"
    if "or higher" in text.lower(): return "↑" + result_str
    elif "or below" in text.lower(): return "↓" + result_str
    return result_str

def get_settled_temp(city_slug, date_str):
    slug = f"highest-temperature-in-{city_slug}-on-{date_str}"
    url = f"https://gamma-api.polymarket.com/events?slug={slug}"
    
    try:
        res = requests.get(url, headers=HEADERS, proxies=PROXIES, timeout=10)
        if res.status_code == 200 and len(res.json()) > 0:
            markets = res.json()[0].get("markets", [])
            max_prob = -1.0
            predicted_title = "--"
            
            for m in markets:
                title = m.get("groupItemTitle", m.get("question", ""))
                resolution = str(m.get("resolution", "")).lower()
                
                temp_match = re.search(r"be (.*?) on", title)
                clean_title = temp_match.group(1) if temp_match else title
                
                # 1. 如果已经明确结算，直接返回绝对事实
                if m.get("winner") is True or resolution in ["yes", "1", "true"]:
                    return normalize_temperature(clean_title) + " (已结算)"
                
                # 2. 如果还没结算，持续追踪最高资金共识的选项
                raw_prices = m.get("outcomePrices")
                if raw_prices:
                    try:
                        prices = json.loads(raw_prices) if isinstance(raw_prices, str) else raw_prices
                        if prices and float(prices[0]) > max_prob:
                            max_prob = float(prices[0])
                            predicted_title = clean_title
                    except: pass
            
            # 3. 未结算情况下的降级输出
            if predicted_title != "--":
                if max_prob >= 0.90:
                    # 超过90%基本就是等待官方盖章的 "In Review" 状态
                    return normalize_temperature(predicted_title) + f" (审核中:{max_prob*100:.0f}%)"
                else:
                    # 尚未打出绝对悬殊概率
                    return normalize_temperature(predicted_title) + f" (未结:{max_prob*100:.0f}%)"
                    
    except Exception as e:
        pass
    return "无数据"

def run_backtest():
    print(f"{'城市':<6} | {'3月27日数据':<18} | {'3月28日数据':<18}")
    print("-" * 55)
    
    for zh_name, slug in CITY_MAP.items():
        print(f"{zh_name:　<4} | ", end="", flush=True) 
        
        temp_27 = get_settled_temp(slug, DATES[0])
        print(f"{temp_27:<18} | ", end="", flush=True)
        
        temp_28 = get_settled_temp(slug, DATES[1])
        print(f"{temp_28:<18}")

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("🚀 启动 Polymarket 链上数据回溯引擎 (资金共识版)...")
    run_backtest()
    print("\n✅ 回溯完成。")