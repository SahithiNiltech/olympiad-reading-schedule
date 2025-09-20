
from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import date, timedelta

app = Flask(__name__)


DATA_FILE = "toggle_data.json"


@app.route("/data")
def data():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return jsonify(data)

# Load or initialize toggle data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        toggle_data = json.load(f)
else:
    toggle_data = {}

# Custom Jinja2 filter to format date strings
from datetime import datetime
def format_date(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return d.strftime("%b %d %Y %a")
app.jinja_env.filters['format_date'] = format_date

def generate_schedule():
    start_date = date(2025, 9, 21)
    end_date = date(2025, 11, 30)

    pages = list(range(5, 165))  # pages 5–164
    total_pages = len(pages)

    total_days = (end_date - start_date).days + 1
    schedule = []

    # Distribute pages as evenly as possible
    base_pages = total_pages // total_days   # 2
    extra_pages = total_pages % total_days   # remainder

    day = start_date
    index = 0

    for d in range(total_days):
        # Some days get 1 extra page
        pages_today = base_pages + (1 if d < extra_pages else 0)
        for _ in range(pages_today):
            schedule.append({"date": str(day), "page": pages[index]})
            index += 1
        day += timedelta(days=1)

    return schedule

schedule = generate_schedule()

@app.route("/")
def index():
    return render_template("index.html", schedule=schedule, toggle_data=toggle_data)

@app.route("/toggle", methods=["POST"])
def toggle():
    data = request.json
    key = f"{data['date']}_{data['page']}"
    toggle_data[key] = not toggle_data.get(key, False)

    with open(DATA_FILE, "w") as f:
        json.dump(toggle_data, f)

    return jsonify({"status": "ok", "toggled": toggle_data[key]})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=9999)
