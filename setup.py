#!/usr/bin/env python3
"""
Setup script for RAG Pipeline API
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def create_directories():
    """Create necessary directories"""
    dirs = ['uploads', 'indexes', 'faiss_index', 'logs']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ Created necessary directories")

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found. Please create one with your API keys.")
        return False
    
    with open(env_file, 'r') as f:
        content = f.read()
        
    required_vars = ['GEMINI_API_KEY', 'SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if var not in content or f"{var}=" not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment file configured")
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up RAG Pipeline API...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        return False
    
    # Create directories
    create_directories()
    
    # Check environment configuration
    if not check_env_file():
        print("\n📝 Please update your .env file with the required variables:")
        print("   - GEMINI_API_KEY: Your Google Gemini API key")
        print("   - SECRET_KEY: A secure secret key for JWT tokens")
        return False
    
    # Initialize database
    if not run_command("python -c \"from app.database import init_db; init_db()\"", "Initializing database"):
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n🚀 To start the API server, run:")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("\n📚 API Documentation will be available at:")
    print("   http://localhost:8000/docs")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
