import os
import random
import sqlite3
from flask import Flask, jsonify, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "super_secret_key_for_demo"

DB_FILE = "game_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # ডেমো ইউজার টেবিল
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
    
    # ডিফল্ট সেটিংস ইনসার্ট করা
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings (id, house_edge, total_bets) VALUES (1, 0.10, 0)")
        
    conn.commit()
    conn.close()

init_db()

# --- HELPER FUNCTIONS ---
def get_settings():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT house_edge, total_bets FROM settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return {"house_edge": row[0], "total_bets": row[1]}

@app.route("/")
def home():
    if "user_logged_in" not in session:
        return redirect(url_for("user_login"))
    
    # ইউজারের বর্তমান ডেমো ব্যালেন্স আনা
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username = ?", (session["username"],))
    balance = cursor.fetchone()[0]
    conn.close()
    
    return render_template("index.html", username=session["username"], balance=balance)

# --- ইউজার সাইনআপ ও লগইন সিস্টেম ---
@app.route("/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            # নতুন ইউজারকে টেস্ট করার জন্য ৫০০০ ডেমো কয়েন/টাকা দেওয়া হচ্ছে
            cursor.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", (username, password, 5000.0))
            conn.commit()
            conn.close()
            return 'Account Created! <a href="/login">Login here</a>'
        except:
            return "Username already exists!"
    return '''
        <form method="post" style="text-align:center; margin-top:100px; font-family:Arial;">
            <h2>Player Registration (Demo)</h2>
            <input type="text" name="username" placeholder="Choose Username" required><br><br>
            <input type="password" name="password" placeholder="Choose Password" required><br><br>
            <button type="submit">Sign Up</button>
        </form>
    '''

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
        return "Invalid Username or Password!"
        
    return '''
        <form method="post" style="text-align:center; margin-top:100px; font-family:Arial;">
            <h2>Player Login (Demo)</h2>
            <input type="text" name="username" placeholder="Username" required><br><br>
            <input type="password" name="password" placeholder="Password" required><br><br>
            <button type="submit">Login</button><br><br>
            <a href="/register">Don't have an account? Register here</a>
        </form>
    '''

@app.route("/logout")
def user_logout():
    session.clear()
    return redirect(url_for("user_login"))

# --- গেম লজিক ---
@app.route("/start-game", methods=["POST"])
def start_game():
    if "user_logged_in" not in session:
        return jsonify({"status": "unauthorized"}), 401
        
    current_settings = get_settings()
    
    # ক্র্যাশ পয়েন্ট জেনারেট করা
    if random.random() < current_settings["house_edge"]:
        crash_point = 1.00
    else:
        e = random.random()
        crash_point = round(max(1.00, 99 / (100 - e * 100)), 2)
        
    return jsonify({"status": "flying", "secret_crash": crash_point})

if __name__ == "__main__":
    app.run(debug=True)
