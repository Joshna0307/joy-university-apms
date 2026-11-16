from app import create_app

# Vercel's Python runtime serves this Flask application as a serverless function.
app = create_app()
