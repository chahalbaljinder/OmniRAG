@echo off
REM Run script for RAG Pipeline Streamlit UI (Windows)

echo 🚀 Starting RAG Pipeline Dashboard
echo ==================================

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo 📥 Installing Streamlit requirements...
pip install -r requirements-streamlit.txt

REM Check if API is running
echo 🔍 Checking API status...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ API is running on http://localhost:8000
) else (
    echo ⚠️  API is not running. Please start the API first:
    echo    python -m uvicorn app.main:app --reload
    echo.
    echo 📖 Starting Streamlit UI anyway...
)

echo.
echo 🌟 Starting Streamlit Dashboard...
echo 📱 Access the UI at: http://localhost:8501
echo 🔧 API Backend at: http://localhost:8000
echo.

REM Start Streamlit
streamlit run streamlit_app.py
