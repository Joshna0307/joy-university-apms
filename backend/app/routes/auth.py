from flask import Blueprint,request,jsonify
from flask_login import current_user,login_user,logout_user,login_required
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import User, Student

auth_bp=Blueprint('auth',__name__)

@auth_bp.post('/register')
def register_student():
    data=request.get_json(silent=True) or {}
    name=(data.get('name') or '').strip()
    email=(data.get('email') or '').strip().lower()
    register_number=(data.get('register_number') or '').strip().upper()
    password=data.get('password') or ''
    if not name or not email or not register_number or not password:
        return jsonify({'error':'Please fill in all fields'}),400
    if not email.endswith('@joyuniversity.edu.in'):
        return jsonify({'error':'Use your official @joyuniversity.edu.in email address'}),400
    if len(password)<12:
        return jsonify({'error':'Password must be at least 12 characters'}),400
    if len(name)>120 or len(email)>255 or len(register_number)>40:
        return jsonify({'error':'One or more fields are too long'}),400
    if User.query.filter_by(email=email).first():
        return jsonify({'error':'An account with this email already exists'}),409
    if Student.query.filter_by(register_number=register_number).first():
        return jsonify({'error':'This register number is already registered'}),409
    user=User(name=name,email=email,role='student',active=True)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.flush()
        student=Student(user_id=user.id,register_number=register_number)
        db.session.add(student)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error':'Email or register number is already in use'}),409
    login_user(user)
    return jsonify({'message':'Student account created','user':user.to_dict()}),201

@auth_bp.post('/login')
def login():
    data=request.get_json(silent=True) or {}
    email=(data.get('email') or '').strip().lower()
    password=data.get('password') or ''
    user=User.query.filter_by(email=email,active=True).first()
    if not user or not user.check_password(password): return jsonify({'error':'Email or password is incorrect'}),401
    login_user(user)
    return jsonify({'user':user.to_dict()})

@auth_bp.get('/me')
def me():
    if not current_user.is_authenticated: return jsonify({'error':'Not signed in'}),401
    return jsonify({'user':current_user.to_dict()})

@auth_bp.post('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message':'Signed out'})
