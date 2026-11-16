from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from config import Config

db=SQLAlchemy()
login_manager=LoginManager()
def create_app():
    app=Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    CORS(app, supports_credentials=True, origins=[os.getenv('FRONTEND_ORIGIN','http://localhost:5173')])
    from app.models import User
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp,url_prefix='/api/auth')
    @app.get('/api/health')
    def health(): return jsonify({'status':'ok','service':'joy-university-apms-api'})
    with app.app_context(): db.create_all()
    return app
import os
