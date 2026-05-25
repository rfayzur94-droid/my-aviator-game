import os
import random
import sqlite3
from flask import Flask, jsonify, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "super_secret_admin_key"

# ডাটাবেজ সেটআপ (ফ্রি সার্ভারে ডাটা স্থায়ী রাখার জন্য SQLite ব্যবহার করা হয়েছে)
DB_FILE = "game_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            house_edge REAL,
            total_bets INTEGER
        )
    ''')
    # ডিফল্ট ডাটা যদি না থাকে
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings (id, house_edge, total_bets) VALUES (1, 0.10, 0)") # ১০% ডিফল্ট রিস্ক
    conn.commit()
    conn.close()

init_db()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "securepassword123"

def get_settings():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT house_edge, total_bets FROM settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return {"house_edge": row[0], "total_bets": row[1]}

def update_db_settings(house_edge):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET house_edge = ? WHERE id = 1", (house_edge,))
    conn.commit()
    conn.close()

def increment_bets():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET total_bets = total_bets + 1 WHERE id = 1")
    conn.commit()
    conn.close()

def generate_crash_point(house_edge):
    if random.random() < house_edge:
        return 1.00
    e = random.random()
    crash_point = 99 / (100 - e * 100)
    return round(max(1.00, crash_point), 2)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/start-game", methods=["POST"])
def start_game():
    increment_bets()
    current_settings = get_settings()
    crash_point = generate_crash_point(current_settings["house_edge"])
    return jsonify({"status": "flying", "secret_crash": crash_point})

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        return "Invalid Credentials!"
    return '''
        <form method="post" style="text-align:center; margin-top:100px; font-family:Arial;">
            <h2>Admin Login</h2>
            <input type="text" name="username" placeholder="Username" required><br><br>
            <input type="password" name="password" placeholder="Password" required><br><br>
            <button type="submit" style="padding:10px 20px; background:#e91e63; color:white; border:none; cursor:pointer;">Login</button>
        </form>
    '''

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    current_settings = get_settings()
    return render_template("admin.html", stats=current_settings)

@app.route("/admin/update-settings", methods=["POST"])
def update_settings():
    if not session.get("admin_logged_in"):
        return jsonify({"status": "unauthorized"}), 401
    new_edge = float(request.form.get("house_edge", 0.10))
    update_db_settings(new_edge)
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True)
