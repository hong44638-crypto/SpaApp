from functools import wraps
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user

from spaapp import app, db, login
from spaapp import dao
from models import seed_data, User, Service, Booking


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


with app.app_context():
    db.create_all()
    seed_data()


def login_required(*roles):

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("login_my_user"))
            if roles and current_user.role not in roles:
                flash("Bạn không có quyền truy cập chức năng này!")
                return redirect(url_for("home"))
            return f(*args, **kwargs)
        return wrapper
    return decorator



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["get", "post"])
def login_my_user():
    if current_user.is_authenticated:
        return redirect("/login")

    err_msg = None
    if request.method.__eq__("POST"):
        username = request.form.get("username")
        password = request.form.get("password")

        user = dao.auth_user(username, password)

        if user:
            login_user(user)
            if user.role == "letan":
                return redirect(url_for("bookings"))

            elif user.role == "ktv":
                return redirect(url_for("tickets"))

            elif user.role == "thungan":
                return redirect(url_for("invoices"))

            elif user.role == "admin":
                return redirect(url_for("reports"))

        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"

    return render_template("login.html", err_msg=err_msg)


@app.route("/logout")
def logout_my_user():
    logout_user()
    return redirect("/")


@app.route("/")
@login_required()
def home():
    return render_template("index.html")


MAX_PER_DAY = 5


@app.route("/bookings")
@login_required("letan", "admin")
def bookings():
    items = Booking.query.order_by(Booking.date, Booking.time).all()
    services = Service.query.all()
    staff = User.query.filter_by(role="ktv").all()
    return render_template("bookings.html", items=items,
                           services=services, staff=staff)


@app.route("/bookings/add", methods=["POST"])
@login_required("letan", "admin")
def add_booking():
    customer = request.form.get("customer_name", "").strip()
    service_id = request.form.get("service_id")
    staff_id = request.form.get("staff_id")
    date = request.form.get("date")
    time = request.form.get("time")

    if not (customer and service_id and staff_id and date and time):
        flash("Vui lòng nhập đầy đủ thông tin!")
        return redirect(url_for("bookings"))

    # Quy định 1: trùng giờ -> từ chối
    if Booking.query.filter_by(staff_id=staff_id, date=date, time=time).first():
        flash("Nhân viên đã có lịch vào giờ này, vui lòng chọn giờ khác!")
        return redirect(url_for("bookings"))

    # Quy định 2: mỗi nhân viên tối đa 5 khách/ngày
    if Booking.query.filter_by(staff_id=staff_id, date=date).count() >= MAX_PER_DAY:
        flash(f"Nhân viên này đã đủ {MAX_PER_DAY} khách trong ngày!")
        return redirect(url_for("bookings"))

    db.session.add(Booking(customer_name=customer, service_id=int(service_id),
                           staff_id=int(staff_id), date=date, time=time))
    db.session.commit()
    flash("Đặt lịch thành công!")
    return redirect(url_for("bookings"))


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



@app.route("/Guest_Booking")
def GuestBooking():
    return render_template("GuestBooking.html")


if __name__ == '__main__':
    app.run(debug=True, port=9999)