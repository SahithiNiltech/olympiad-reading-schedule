from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import date, timedelta
import sqlite3

app = Flask(__name__)


# SQLite setup
DB_FILE = "toggle_data.db"
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize table if not exists
def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS toggles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            page INTEGER NOT NULL,
            status INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()
init_db()

def get_toggle_data():
    conn = get_db()
    rows = conn.execute("SELECT date, page, status FROM toggles").fetchall()
    conn.close()
    return {f"{row['date']}_{row['page']}": bool(row['status']) for row in rows}

def set_toggle(date, page, status):
    conn = get_db()
    result = conn.execute("UPDATE toggles SET status=? WHERE date=? AND page=?", (int(status), date, page))
    if result.rowcount == 0:
        conn.execute("INSERT INTO toggles (date, page, status) VALUES (?, ?, ?)", (date, page, int(status)))
    conn.commit()
    conn.close()

@app.route("/data")
def data():
    return jsonify(get_toggle_data())

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
    toggle_data = get_toggle_data()
    return render_template("index.html", schedule=schedule, toggle_data=toggle_data)

@app.route("/toggle", methods=["POST"])
def toggle():
    data = request.json
    date = data['date']
    page = int(data['page'])
    toggle_data = get_toggle_data()
    key = f"{date}_{page}"
    toggled = not toggle_data.get(key, False)
    set_toggle(date, page, toggled)
    return jsonify({"status": "ok", "toggled": toggled})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=9999)
