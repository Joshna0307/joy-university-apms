import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

database_url = os.getenv("DATABASE_URL", "sqlite:///apms-dev.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

is_production = os.getenv("FLASK_ENV") == "production"

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "local-development-only-change-me")
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "None" if is_production else "Lax"
    SESSION_COOKIE_SECURE = is_production
