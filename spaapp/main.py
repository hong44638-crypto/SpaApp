from functools import wraps
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user

from spaapp import app, db, login
from spaapp import dao
from models import seed_data, User, Service, Booking, Ticket


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
        return redirect("/")

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

MAX_PER_DAY=5

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


    if Booking.query.filter_by(staff_id=staff_id, date=date, time=time).first():
        flash("Nhân viên đã có lịch vào giờ này, vui lòng chọn giờ khác!")
        return redirect(url_for("bookings"))


    if Booking.query.filter_by(staff_id=staff_id, date=date).count() >= MAX_PER_DAY:
        flash(f"Nhân viên này đã đủ {MAX_PER_DAY} khách trong ngày!")
        return redirect(url_for("bookings"))

    db.session.add(Booking(customer_name=customer, service_id=int(service_id),
                           staff_id=int(staff_id), date=date, time=time))
    db.session.commit()
    flash("Đặt lịch thành công!")
    return redirect(url_for("bookings"))


@app.route("/tickets", methods=["GET", "POST"])
@login_required("ktv", "admin")
def tickets():
    if request.method == "POST":
        customer = request.form.get("customer_name", "").strip()
        service_id = request.form.get("service_id",type=int)
        duration = request.form.get("duration",type=int)
        note = request.form.get("note","").strip()
        service = db.session.get(Service, service_id) if service_id else None
        if not customer:
            flash("Vui lòng nhập tên khách hàng!","error")
        elif not service:
            flash("Dịch vụ không hợp lệ!","error")
        elif duration is None or not (15<= duration <=120):
            flash("Thời lượng phải từ 15 đến 120 phút!","error")
        else:
            db.session.add(Ticket(
                customer_name=customer, service_id=service.id,
                staff_id=current_user.id, duration=duration,
                price=service.price, note=note,
            ))
            db.session.commit()
            flash("Đã lưu phiếu dịch vụ!","success")
        return redirect(url_for("tickets"))
    services = Service.query.all()
    ticket_list = Ticket.query.order_by(Ticket.id.desc()).all()
    return render_template("tickets.html", services=services, tickets=ticket_list)
@app.template_filter("vnd")
def vnd(value):
    return f"{value:,}".replace(",", ".")


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



@app.route("/GuestBooking")
def guest_booking():
    services = Service.query.all()
    staff = User.query.filter_by(role="ktv").all()
    return render_template("GuestBooking.html",
                           services=services, staff=staff)


@app.route("/GuestBooking/add", methods=["POST"])
def guest_add_booking():
    customer = request.form.get("customer_name", "").strip()
    service_id = request.form.get("service_id")
    staff_id = request.form.get("staff_id")
    date = request.form.get("date")
    time = request.form.get("time")

    if not (customer and service_id and staff_id and date and time):
        flash("Vui lòng nhập đầy đủ thông tin!")
        return redirect(url_for("guest_booking"))

    if Booking.query.filter_by(staff_id=staff_id, date=date, time=time).first():
        flash("Nhân viên đã có lịch vào giờ này, vui lòng chọn giờ khác!")
        return redirect(url_for("guest_booking"))

    if Booking.query.filter_by(staff_id=staff_id, date=date).count() >= MAX_PER_DAY:
        flash(f"Nhân viên này đã đủ {MAX_PER_DAY} khách trong ngày!")
        return redirect(url_for("guest_booking"))

    db.session.add(Booking(customer_name=customer, service_id=int(service_id),
                           staff_id=int(staff_id), date=date, time=time,
                           status="Chờ xác nhận"))
    db.session.commit()
    flash("Đặt lịch thành công! Spa sẽ liên hệ xác nhận với bạn.")
    return redirect(url_for("guest_booking"))

@app.route("/bookings/confirm/<int:booking_id>", methods=["POST"])
@login_required("letan", "admin")
def confirm_booking(booking_id):
    b = Booking.query.get_or_404(booking_id)
    if b.status == "Chờ xác nhận":
        b.status = "Đã xác nhận"
        db.session.commit()
        flash(f"Đã xác nhận lịch của khách {b.customer_name}.")
    return redirect(url_for("bookings"))
if __name__ == '__main__':
    app.run(debug=True, port=9999)