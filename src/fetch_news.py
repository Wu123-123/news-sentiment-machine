import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import time

API_KEY = os.getenv("NEWS_API_KEY")
if not API_KEY:
    with open(".env") as f:
        for line in f:
            if line.startswith("NEWS_API_KEY"):
                API_KEY = line.strip().split("=", 1)[1]

def _fetch_one_day(keyword, date_str):
    """Fetch articles for a single date (YYYY-MM-DD). Returns list of rows."""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": keyword,
        "from": date_str,
        "to": date_str,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 100,
        "apiKey": API_KEY,
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    if data.get("status") != "ok":
        print(f"  [{date_str}] Error: {data.get('message')}")
        return []
    return [
        {
            "date": a["publishedAt"][:10],
            "title": a["title"],
            "source": a["source"]["name"],
            "url": a["url"],
        }
        for a in data.get("articles", [])
        if a.get("title") and "[Removed]" not in a.get("title", "")
    ]

def fetch_news(keyword="stock market", days=30):
    """Fetch news day-by-day for the past `days` days and save one CSV per day."""
    os.makedirs("data", exist_ok=True)
    today = datetime.today()
    saved = 0
    for i in range(days, 0, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        filename = f"data/news_{keyword.replace(' ', '_')}_{d.replace('-', '')}.csv"
        if os.path.exists(filename):
            print(f"  跳过（已存在）: {filename}")
            continue
        rows = _fetch_one_day(keyword, d)
        if rows:
            pd.DataFrame(rows).to_csv(filename, index=False)
            print(f"  保存: {filename}，{len(rows)} 条")
            saved += 1
        else:
            print(f"  [{d}] 无数据")
        time.sleep(0.3)   # be gentle with the API
    print(f"完成：新增 {saved} 个文件（关键词: {keyword}）")

if __name__ == "__main__":
    fetch_news("stock market", days=30)
    fetch_news("nasdaq", days=30)
