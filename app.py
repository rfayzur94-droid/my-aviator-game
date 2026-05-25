import random
from flask import Flask, jsonify, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "super_secret_admin_key"

game_stats = {
    "total_bets": 0,
    "total_payout": 0,
    "house_edge": 0.03,
}

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "securepassword123"

def generate_crash_point():
    if random.random() < game_stats["house_edge"]:
        return 1.00
    e = random.random()
    crash_point = 99 / (100 - e * 100)
    return round(max(1.00, crash_point), 2)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/start-game", methods=["POST"])
def start_game():
    game_stats["total_bets"] += 1
    crash_point = generate_crash_point()
    return jsonify({"status": "flying", "secret_crash": crash_point})

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        return "Invalid Credentials!"
    return '''
        <form method="post" style="text-align:center; margin-top:100px;">
            <h2>Admin Login</h2>
            <input type="text" name="username" placeholder="Username" required><br><br>
            <input type="password" name="password" placeholder="Password" required><br><br>
            <button type="submit">Login</button>
        </form>
    '''

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    return render_template("admin.html", stats=game_stats)

@app.route("/admin/update-settings", methods=["POST"])
def update_settings():
    if not session.get("admin_logged_in"):
        return jsonify({"status": "unauthorized"}), 401
    new_edge = float(request.form.get("house_edge", 0.03))
    game_stats["house_edge"] = new_edge
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True)
