import os
import random
import sqlite3
from flask import Flask, jsonify, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "super_secret_aviator_key_2026"

DB_FILE = "game_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # ইউজার টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            balance REAL
        )
    ''')
    # গেম সেটিংস টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            house_edge REAL,
            total_bets INTEGER
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings (id, house_edge, total_bets) VALUES (1, 0.10, 0)")
    conn.commit()
    conn.close()

init_db()

def get_settings():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT house_edge, total_bets FROM settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return {"house_edge": row[0], "total_bets": row[1]}

# --- রুট সমূহ ---

@app.route("/")
def home():
    if "user_logged_in" not in session:
        return redirect(url_for("user_login"))
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username = ?", (session["username"],))
    row = cursor.fetchone()
    balance = row[0] if row else 0.0
    conn.close()
    
    return render_template("index.html", username=session["username"], balance=balance)

@app.route("/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] == password:
            session["user_logged_in"] = True
            session["username"] = username
            return redirect(url_for("home"))
        return "ভুল ইউজারনেম বা পাসওয়ার্ড! <a href='/login'>আবার চেষ্টা করুন</a>"
        
    return '''
        <body style="background:#0f0f12; color:white; font-family:Arial; text-align:center; padding-top:100px;">
            <h2>Aviator Player Login</h2>
            <form method="post" style="background:#14151a; display:inline-block; padding:30px; border-radius:10px;">
                <input type="text" name="username" placeholder="Username" style="padding:10px; margin:10px;" required><br>
                <input type="password" name="password" placeholder="Password" style="padding:10px; margin:10px;" required><br>
                <button type="submit" style="padding:10px 20px; background:#28a745; color:white; border:none; cursor:pointer;">Login</button>
            </form><br><br>
            <a href="/register" style="color:#aaa;">নতুন অ্যাকাউন্ট খুলুন (Register)</a>
        </body>
    '''

@app.route("/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", (username, password, 5000.0))
            conn.commit()
            conn.close()
            return 'অ্যাকাউন্ট তৈরি হয়েছে! <a href="/login">এখানে লগইন করুন</a>'
        except:
            return "এই ইউজারনেম অলরেডি আছে! <a href='/register'>অন্য নাম দিন</a>"
            
    return '''
        <body style="background:#0f0f12; color:white; font-family:Arial; text-align:center; padding-top:100px;">
            <h2>Aviator Player Registration</h2>
            <form method="post" style="background:#14151a; display:inline-block; padding:30px; border-radius:10px;">
                <input type="text" name="username" placeholder="Choose Username" style="padding:10px; margin:10px;" required><br>
                <input type="password" name="password" placeholder="Choose Password" style="padding:10px; margin:10px;" required><br>
                <button type="submit" style="padding:10px 20px; background:#e91e63; color:white; border:none; cursor:pointer;">Sign Up</button>
            </form><br><br>
            <a href="/login" style="color:#aaa;">অলরেডি অ্যাকাউন্ট আছে? লগইন করুন</a>
        </body>
    '''

@app.route("/logout")
def user_logout():
    session.clear()
    return redirect(url_for("user_login"))

@app.route("/start-game", methods=["POST"])
def start_game():
    if "user_logged_in" not in session:
        return jsonify({"status": "unauthorized"}), 401
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET total_bets = total_bets + 1 WHERE id = 1")
    conn.commit()
    conn.close()
    
    current_settings = get_settings()
    if random.random() < current_settings["house_edge"]:
        crash_point = 1.00
    else:
        e = random.random()
        crash_point = round(max(1.00, 99 / (100 - e * 100)), 2)
        
    return jsonify({"status": "flying", "secret_crash": crash_point})

# --- এডমিন সেকশন ---
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "securepassword123":
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        return "ভুল এডমিন তথ্য! <a href='/admin/login'>আবার চেষ্টা করুন</a>"
    return '''
        <body style="background:#0f0f12; color:white; font-family:Arial; text-align:center; padding-top:100px;">
            <h2>Admin Login Panel</h2>
            <form method="post" style="background:#1c1d24; display:inline-block; padding:30px; border-radius:10px;">
                <input type="text" name="username" placeholder="Admin Username" style="padding:10px; margin:10px;" required><br>
                <input type="password" name="password" placeholder="Admin Password" style="padding:10px; margin:10px;" required><br>
                <button type="submit" style="padding:10px 20px; background:#e91e63; color:white; border:none; cursor:pointer;">Login</button>
            </form>
        </body>
    '''

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    current_settings = get_settings()
    return render_template("admin.html", stats=current_settings)

if __name__ == "__main__":
    app.run(debug=True)
