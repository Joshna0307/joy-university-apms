import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    if os.getenv("FLASK_ENV") == "production":
        missing = [key for key in ("DATABASE_URL", "SECRET_KEY", "FRONTEND_ORIGIN") if not os.getenv(key)]
        if missing:
            raise RuntimeError("Missing required production environment variables: " + ", ".join(missing))
    db.init_app(app)
    login_manager.init_app(app)
    CORS(
        app,
        supports_credentials=True,
        origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    )

    from app import models  # noqa: F401 - register all SQLAlchemy models
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.attendance import attendance_bp
    from app.routes.admin import admin_bp
    from app.routes.academics import academics_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(academics_bp, url_prefix="/api/academics")

    @app.get("/api/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            db.session.rollback()
            return jsonify({"status": "error", "database": "unavailable"}), 503
        return jsonify({"status": "ok", "database": "connected", "service": "joy-university-apms-api"})

    with app.app_context():
        db.create_all()
    return app
