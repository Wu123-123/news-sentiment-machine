from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
import glob
import json
import os
from deep_translator import GoogleTranslator

app = Flask(__name__)

# ── Seed 30-day history if no daily files exist ───────────────────────────────
def _seed_history():
    if glob.glob("data/*_daily.csv"):
        return
    os.makedirs("data", exist_ok=True)
    rng = np.random.default_rng(42)
    from datetime import date, timedelta
    today = date.today()
    rows = [
        {"date": (today - timedelta(days=i)).isoformat(),
         "avg_score": round(float(np.clip(rng.normal(0, 0.18), -0.6, 0.6)), 4),
         "count": int(rng.integers(60, 120))}
        for i in range(30, 0, -1)
    ]
    pd.DataFrame(rows).to_csv("data/history_30d_daily.csv", index=False)

_seed_history()

# ── Translation cache (disk-backed) ──────────────────────────────────────────
CACHE_FILE = "data/translations_cache.json"

def _load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

_cache = _load_cache()
_translator = GoogleTranslator(source="en", target="zh-CN")

def translate(text: str) -> str:
    if not text:
        return text
    if text in _cache:
        return _cache[text]
    try:
        result = _translator.translate(text)
        _cache[text] = result
        _save_cache(_cache)
        return result
    except Exception:
        return text

# ── Data helpers ──────────────────────────────────────────────────────────────
def load_daily_data():
    files = glob.glob("data/*_daily.csv")
    if not files:
        return []
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df = df.groupby("date", as_index=False).agg(
        avg_score=("avg_score", "mean"),
        count=("count", "sum")
    )
    df = df.sort_values("date")
    return df.to_dict(orient="records")

def load_headlines(date):
    files = glob.glob("data/*_analyzed.csv")
    if not files:
        return []
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    cols = [c for c in ["title", "sentiment_score", "sentiment_label", "url", "source"] if c in df.columns]
    day_df = (
        df[df["date"] == date][cols]
        .drop_duplicates("title")
        .sort_values("sentiment_score", key=abs, ascending=False)
        .head(20)
    )
    records = day_df.to_dict(orient="records")
    for r in records:
        r["title_zh"] = translate(r.get("title", ""))
    return records

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    return jsonify(load_daily_data())

@app.route("/api/headlines")
def api_headlines():
    date = request.args.get("date", "")
    return jsonify(load_headlines(date))

if __name__ == "__main__":
    app.run(debug=True, port=8080)
