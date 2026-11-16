"""Create the first administrator without storing credentials in source.

Run from the backend folder with: python -m scripts.create_admin
"""
import getpass
import re
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    email = input("Administrator email: ").strip().lower()
    name = input("Administrator name: ").strip()
    password = getpass.getpass("Choose a strong password (min 12 characters): ")
    confirm = getpass.getpass("Confirm password: ")

    if not re.fullmatch(r"[^@\s]+@joyuniversity\.edu\.in", email):
        raise SystemExit("Use an official @joyuniversity.edu.in email address.")
    if not name:
        raise SystemExit("Name is required.")
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    if password != confirm:
        raise SystemExit("Passwords do not match.")
    if User.query.filter_by(email=email).first():
        raise SystemExit("An account with this email already exists.")

    admin = User(name=name, email=email, role="admin", active=True)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f"Administrator created: {email}")
