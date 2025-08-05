# Vercel serverless handler
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.main import app

# This is required for Vercel serverless functions
handler = app
