from flask import Blueprint,request,jsonify
from flask_login import current_user,login_user,logout_user,login_required
from app import db
from app.models import User
auth_bp=Blueprint('auth',__name__)
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
