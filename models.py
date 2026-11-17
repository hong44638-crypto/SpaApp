from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy()

class User(db.Model):                      # tài khoản + nhân viên
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)   # letan / ktv / thungan / admin

class Service(db.Model):                   # dịch vụ
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)   # phút, 15-120
    price = db.Column(db.Integer, nullable=False)

class Booking(db.Model):                   # lịch đặt
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.String(10), nullable=False)    # YYYY-MM-DD
    time = db.Column(db.String(5), nullable=False)     # HH:MM
    status = db.Column(db.String(20), default="Đã xác nhận")
    service = db.relationship("Service")
    staff = db.relationship("User")

def seed_data():
    """Tạo dữ liệu mẫu lần đầu"""
    if User.query.first():
        return
    db.session.add_all([
        User(username="admin", full_name="Quản trị", role="admin",
             password_hash=generate_password_hash("123456")),
        User(username="letan", full_name="Lê Tân", role="letan",
             password_hash=generate_password_hash("123456")),
        User(username="thungan", full_name="Thu Ngân", role="thungan",
             password_hash=generate_password_hash("123456")),
        User(username="hong", full_name="Nguyễn Hồng", role="ktv",
             password_hash=generate_password_hash("123456")),
        Service(code="DV001", name="Massage Body", duration=60, price=400000),
        Service(code="DV002", name="Massage mặt", duration=45, price=300000),
    ])
    db.session.commit()