import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production")

# ─── Database connection ──────────────────────────────────────────────────────
def get_db():
    return pymysql.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASS"),
        database=os.environ.get("DB_NAME"),
        port=int(os.environ.get("DB_PORT", 3306)),  # ✅ ADD THIS
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,

        # ✅ REQUIRED for Aiven
        ssl={
            "ssl": {
                "ca": "/etc/ssl/certs/ca-certificates.crt"
            }
        }
    )

def init_db():
    """Create the users table if it doesn't exist."""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id        INT AUTO_INCREMENT PRIMARY KEY,
                username  VARCHAR(80)  NOT NULL UNIQUE,
                email     VARCHAR(120) NOT NULL UNIQUE,
                password  VARCHAR(256) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.close()


# ─── Auth helpers ─────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        # Basic validation
        if not all([username, email, password, confirm]):
            flash("All fields are required.", "error")
            return render_template("signup.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("signup.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("signup.html")

        hashed = generate_password_hash(password)

        try:
            conn = get_db()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, hashed),
                )
            conn.close()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))

        except pymysql.err.IntegrityError as e:
            if "username" in str(e):
                flash("Username already taken.", "error")
            else:
                flash("Email already registered.", "error")
        except Exception as e:
            flash(f"Database error: {e}", "error")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password   = request.form.get("password", "")

        try:
            conn = get_db()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM users WHERE email = %s OR username = %s",
                    (identifier.lower(), identifier),
                )
                user = cur.fetchone()
            conn.close()

            if user and check_password_hash(user["password"], password):
                session["user_id"]  = user["id"]
                session["username"] = user["username"]
                flash(f"Welcome back, {user['username']}!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid credentials. Please try again.", "error")

        except Exception as e:
            flash(f"Database error: {e}", "error")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session["username"])


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# ─── Startup ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
