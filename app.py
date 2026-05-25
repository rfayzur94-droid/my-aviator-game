import os
import random
import sqlite3
from flask import Flask, jsonify, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "ultimate_secure_aviator_key_2026"
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
    # ট্রানজেকশন টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            type TEXT,
            method TEXT,
            number TEXT,
            amount REAL,
            txid TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

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

@app.route("/transaction", methods=["POST"])
def handle_transaction():
    if "user_logged_in" not in session:
        return jsonify({"status": "unauthorized"}), 401
        
    tx_type = request.form.get("type")
    method = request.form.get("method")
    number = request.form.get("number")
    amount = float(request.form.get("amount", 0))
    txid = request.form.get("txid", "N/A")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (username, type, method, number, amount, txid, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending')
    ''', (session["username"], tx_type, method, number, amount, txid))
    
    if tx_type == "withdraw":
        cursor.execute("UPDATE users SET balance = balance - ? WHERE username = ?", (amount, session["username"]))
        
    conn.commit()
    conn.close()
    return redirect(url_for("home"))

@app.route("/start-game", methods=["POST"])
def start_game():
    if "user_logged_in" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    # ১০% চান্স গেম ১.০০x এ ক্র্যাশ করবে
    if random.random() < 0.10:
        crash_point = 1.00
    else:
        crash_point = round(random.uniform(1.05, 4.50), 2)
        
    return jsonify({"status": "flying", "secret_crash": crash_point})

@app.route("/game-result", methods=["POST"])
def game_result():
    if "user_logged_in" not in session:
        return jsonify({"status": "unauthorized"}), 401
        
    data = request.json
    action = data.get("action")
    bet_amount = float(data.get("bet_amount", 0))
    rate = float(data.get("rate", 1.00))
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if action == "loss":
        cursor.execute("UPDATE users SET balance = balance - ? WHERE username = ?", (bet_amount, session["username"]))
    elif action == "cashout":
        winnings = bet_amount * rate
        profit = winnings - bet_amount
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (profit, session["username"]))
        
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})

# --- ইউজার লগইন/সাইনআপ ---
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
        return "ভুল তথ্য! <a href='/login'>আবার চেষ্টা করুন</a>"
    return '<body style="background:#0f0f12;color:white;text-align:center;font-family:Arial;padding-top:50px;"><h2>Player Login</h2><form method="post"><input type="text" name="username" placeholder="Username" required><br><br><input type="password" name="password" placeholder="Password" required><br><br><button type="submit">Login</button></form><br><a href="/register" style="color:#aaa;">Register</a></body>'

@app.route("/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, 1000.0)", (username, password))
            conn.commit()
            conn.close()
            return 'অ্যাকাউন্ট তৈরি! <a href="/login">লগইন করুন</a>'
        except:
            return "ইউজারনেম অলরেডি আছে!"
    return '<body style="background:#0f0f12;color:white;text-align:center;font-family:Arial;padding-top:50px;"><h2>Register</h2><form method="post"><input type="text" name="username" placeholder="Username" required><br><br><input type="password" name="password" placeholder="Password" required><br><br><button type="submit">Sign Up</button></form></body>'

# --- এডমিন সেকশন (কানেকশন ফিক্সড) ---
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
        
    # ডাটাবেজ থেকে প্লেয়ারদের পাঠানো ট্রানজেকশন লিস্ট আনা
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, type, method, number, amount, txid, status FROM transactions ORDER BY id DESC")
    tx_list = cursor.fetchall()
    conn.close()
    
    return render_template("admin.html", list=tx_list)

@app.route("/logout")
def user_logout():
    session.clear()
    return redirect(url_for("user_login"))

if __name__ == "__main__":
    app.run(debug=True)
