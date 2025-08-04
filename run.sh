#!/bin/bash
# Run script for RAG Pipeline Streamlit UI

echo "🚀 Starting RAG Pipeline Dashboard"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing Streamlit requirements..."
pip install -r requirements-streamlit.txt

# Check if API is running
echo "🔍 Checking API status..."
curl -s http://localhost:8000/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ API is running on http://localhost:8000"
else
    echo "⚠️  API is not running. Please start the API first:"
    echo "   python -m uvicorn app.main:app --reload"
    echo ""
    echo "📖 Starting Streamlit UI anyway..."
fi

echo ""
echo "🌟 Starting Streamlit Dashboard..."
echo "📱 Access the UI at: http://localhost:8501"
echo "🔧 API Backend at: http://localhost:8000"
echo ""

# Start Streamlit
streamlit run streamlit_app.py
