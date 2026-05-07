from flask import Flask, render_template, jsonify, request
import pandas as pd
import glob

app = Flask(__name__)

def load_daily_data():
    files = glob.glob("data/*_daily.csv")
    if not files:
        return []
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df = df.groupby("date", as_index=False).agg(avg_score=("avg_score", "mean"), count=("count", "sum"))
    df = df.sort_values("date")
    return df.to_dict(orient="records")

def load_headlines(date):
    files = glob.glob("data/*_analyzed.csv")
    if not files:
        return []
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    day_df = df[df["date"] == date][["title", "sentiment_score", "url"]].drop_duplicates("title").head(10)
    return day_df.to_dict(orient="records")

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
