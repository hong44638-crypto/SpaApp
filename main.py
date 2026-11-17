from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from models import db, User, seed_data

app = Flask(__name__)
app.secret_key = "hongdo29"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:123456@localhost:3306/spa_db?charset=utf8mb4"
db.init_app(app)

with app.app_context():
    db.create_all()
    seed_data()


def login_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "username" not in session:
                return redirect(url_for("login"))
            if roles and session["role"] not in roles:
                flash("Bạn không có quyền truy cập chức năng này!")
                return redirect(url_for("home"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get("username", "").strip()).first()
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            session["username"] = user.username
            session["full_name"] = user.full_name
            session["role"] = user.role
            return redirect(url_for("home"))
        flash("Sai tên đăng nhập hoặc mật khẩu!")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required()
def home():
    return render_template("index.html")


@app.route("/bookings")
@login_required("letan", "admin")
def bookings():
    return render_template("bookings.html")


@app.route("/tickets")
@login_required("ktv", "admin")
def tickets():
    return render_template("tickets.html")


@app.route("/invoices")
@login_required("thungan", "admin")
def invoices():
    return render_template("invoices.html")


@app.route("/reports")
@login_required("admin")
def reports():
    return render_template("reports.html")


@app.route("/settings")
@login_required("admin")
def settings():
    return render_template("settings.html")


if __name__ == '__main__':
    app.run(debug=True, port=9999)