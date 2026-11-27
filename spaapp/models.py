from datetime import datetime
import hashlib
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from spaapp import app, db


class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)   # phút, 15-120
    price = db.Column(db.Integer, nullable=False)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(5), nullable=False)
    status = db.Column(db.String(20), default="Đã xác nhận")
    service = db.relationship("Service")
    staff = db.relationship("User")

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    duration= db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(200))
    date = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    service = db.relationship("Service")
    staff = db.relationship("User")

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("ticket.id"),
                              unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    service_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    discount = db.Column(db.Integer, default=0)
    vat = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    date= db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    ticket = db.relationship("Ticket")

class Setting(db.Model):
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(50), nullable=False)

def seed_data():

    if User.query.first():
        return
    pw = hashlib.md5("123456".encode("utf-8")).hexdigest()
    db.session.add_all([
        User(username="admin", full_name="Quản trị", role="admin", password_hash=pw),
        User(username="letan", full_name="Lê Tân", role="letan", password_hash=pw),
        User(username="thungan", full_name="Thu Ngân", role="thungan", password_hash=pw),
        User(username="hong", full_name="Xuân Hồng", role="ktv", password_hash=pw),
        User(username="vinh",full_name="Đắc Vinh",role="ktv",password_hash=pw),
        Service(code="DV001", name="Massage Body", duration=60, price=400000),
        Service(code="DV002", name="Massage mặt", duration=45, price=300000),
    ])
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        seed_data()
        db.create_all()
