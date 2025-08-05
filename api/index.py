# Vercel serverless handler
from app.main import app

# This is required for Vercel serverless functions
handler = app
