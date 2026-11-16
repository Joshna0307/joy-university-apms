import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / '.env')
class Config:
    SECRET_KEY=os.getenv('SECRET_KEY','local-development-only-change-me')
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL','sqlite:///apms-dev.db')
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SESSION_COOKIE_HTTPONLY=True
    SESSION_COOKIE_SAMESITE='Lax'
    SESSION_COOKIE_SECURE=os.getenv('FLASK_ENV')=='production'
