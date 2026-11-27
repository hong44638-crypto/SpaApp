from functools import wraps
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user

from spaapp import app, db, login
from spaapp import dao
from models import seed_data, User, Service, Booking, Ticket, Invoice, Setting
from datetime import datetime
from sqlalchemy import func


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

DEFAULTS = {"vat_percent": 10, "max_per_day": 5, "max_discount_percent": 20}


def get_setting(key):
    s = db.session.get(Setting, key)
    return float(s.value) if s else float(DEFAULTS[key])


def set_setting(key, value):
    s = db.session.get(Setting, key)
    if s:
        s.value = str(value)
    else:
        db.session.add(Setting(key=key, value=str(value)))




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

    MAX_PER_DAY = int(get_setting("max_per_day"))

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
        date = request.form.get("date") or datetime.now().strftime("%Y-%m-%d")
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
                price=service.price, note=note,date=date,
            ))
            db.session.commit()
            flash("Đã lưu phiếu dịch vụ!","success")
        return redirect(url_for("tickets"))
    services = Service.query.all()
    ticket_list = Ticket.query.order_by(Ticket.id.desc()).all()
    return render_template("tickets.html", services=services, tickets=ticket_list)


@app.route("/invoices")
@login_required("thungan", "admin")

def invoices():
    MAX_DISCOUNT = get_setting("max_discount_percent")
    VAT_RATE = get_setting("vat_percent")/100
    invoiced_ids = db.session.query(Invoice.ticket_id)
    pending = Ticket.query.filter(~Ticket.id.in_(invoiced_ids)) \
                          .order_by(Ticket.created_at).all()
    items = Invoice.query.order_by(Invoice.created_at.desc()).all()
    return render_template("invoices.html", pending=pending, items=items,
                           max_percent=int(MAX_DISCOUNT ))


@app.route("/invoices/create/<int:ticket_id>", methods=["POST"])
@login_required("thungan", "admin")
def create_invoice(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    MAX_DISCOUNT = get_setting("max_discount_percent")
    VAT_RATE = get_setting("vat_percent")/100

    if Invoice.query.filter_by(ticket_id=ticket.id).first():
        flash("Phiếu này đã được lập hóa đơn!")
        return redirect(url_for("invoices"))

    try:
        percent = float(request.form.get("discount_percent") or 0)
    except ValueError:
        flash("Giảm giá không hợp lệ!")
        return redirect(url_for("invoices"))

    if percent < 0:
        flash("Giảm giá không được âm!")
        return redirect(url_for("invoices"))

    if percent > MAX_DISCOUNT * 100:
        flash(f"Giảm giá tối đa {int(MAX_DISCOUNT * 100)}% mỗi dịch vụ!")
        return redirect(url_for("invoices"))

    price = ticket.price
    discount = round(price * percent / 100)  # đổi % thành số tiền
    vat = round((price - discount) * VAT_RATE)
    total = price - discount + vat

    db.session.add(Invoice(ticket_id=ticket.id,
                           customer_name=ticket.customer_name,
                           service_name=ticket.service.name,
                           price=price, discount=discount,
                           date=ticket.date,
                           vat=vat, total=total))
    db.session.commit()
    flash(f"Đã lập hóa đơn cho khách {ticket.customer_name}.")
    return redirect(url_for("invoices"))

@app.route("/settings", methods=["GET", "POST"])
@login_required("admin")
def settings():
    if request.method == "POST":
        try:
            vat = float(request.form["vat_percent"])
            per_day = int(request.form["max_per_day"])
            max_disc = float(request.form["max_discount_percent"])
        except (ValueError, KeyError):
            flash("Dữ liệu không hợp lệ!")
            return redirect(url_for("settings"))

        if not (0 <= vat <= 100 and 1 <= per_day <= 50 and 0 <= max_disc <= 100):
            flash("Giá trị nằm ngoài phạm vi cho phép!")
            return redirect(url_for("settings"))

        set_setting("vat_percent", vat)
        set_setting("max_per_day", per_day)
        set_setting("max_discount_percent", max_disc)
        db.session.commit()
        flash("Đã cập nhật quy định.")
        return redirect(url_for("settings"))

    return render_template("settings.html",
                           vat=get_setting("vat_percent"),
                           per_day=int(get_setting("max_per_day")),
                           max_disc=get_setting("max_discount_percent"),
                           services=Service.query.all())


@app.route("/settings/service/<int:service_id>", methods=["POST"])
@login_required("admin")
def update_service_price(service_id):
    sv = Service.query.get_or_404(service_id)
    try:
        price = int(request.form["price"])
    except (ValueError, KeyError):
        flash("Giá không hợp lệ!")
        return redirect(url_for("settings"))
    if price <= 0:
        flash("Giá phải lớn hơn 0!")
        return redirect(url_for("settings"))
    sv.price = price
    db.session.commit()
    flash(f"Đã cập nhật giá dịch vụ {sv.name}.")
    return redirect(url_for("settings"))



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
    MAX_PER_DAY = get_setting("max_per_day")

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

@app.route("/reports")
@login_required("admin")
def reports():
    month = request.args.get("month") or datetime.now().strftime("%Y-%m")
    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        flash("Tháng không hợp lệ!")
        return redirect(url_for("reports"))

    in_month = (Invoice.date.like(f"{month}-%"),)

    total_revenue = db.session.query(func.coalesce(func.sum(Invoice.total), 0)) \
                              .filter(*in_month).scalar()
    invoice_count = Invoice.query.filter(*in_month).count()

    usage = db.session.query(Invoice.service_name,
                             func.count(Invoice.id),
                             func.sum(Invoice.total)) \
                      .filter(*in_month) \
                      .group_by(Invoice.service_name) \
                      .order_by(func.count(Invoice.id).desc()).all()

    return render_template("reports.html", month=month, usage=usage,
                           total_revenue=total_revenue,
                           invoice_count=invoice_count)
if __name__ == '__main__':
    app.run(debug=True, port=9999)