import hashlib
from models import db, User


def add_user(full_name, username, password, role):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    u = User(full_name=full_name, username=username,
             password_hash=password, role=role)
    db.session.add(u)
    db.session.commit()
    return u


def auth_user(username, password):
    if not username or not password:
        return None
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    return User.query.filter(User.username == username.strip(),
                             User.password_hash == password).first()


def get_user_by_id(user_id):
    return db.session.get(User, int(user_id))


if __name__ == "__main__":
    from main import app
    with app.app_context():
        add_user(full_name="letan", username="letan",
                 password="123456", role="letan")
        print("Da tao tai khoan")