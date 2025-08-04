# 🎨 Streamlit UI Setup Guide

This guide will help you set up and run the comprehensive Streamlit UI for the RAG Pipeline.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Docker Setup](#docker-setup)
- [Usage Guide](#usage-guide)
- [API Configuration](#api-configuration)
- [Troubleshooting](#troubleshooting)

## 🔍 Overview

The Streamlit UI provides a comprehensive web interface for the RAG Pipeline with the following capabilities:

- **Authentication**: User registration, login, and JWT token management
- **Document Management**: Upload, view, and delete PDF documents
- **Query Interface**: Ask questions with advanced search options
- **API Key Management**: Create and manage API keys for programmatic access
- **System Monitoring**: Real-time performance metrics and system statistics

## ✨ Features

### 🔐 Authentication System
- User registration and login
- JWT token-based authentication
- Session management
- Secure logout

### 📄 Document Management
- Multi-file PDF upload
- Async processing support
- Document listing with metadata
- Document deletion with confirmation
- Real-time upload progress

### 🔍 Query Interface
- Natural language queries
- Multiple search types (hybrid, semantic, keyword)
- Configurable result count
- Cache management
- Query expansion
- Response time metrics

### 🔑 API Key Management
- Create API keys with custom expiration
- Secure key generation
- One-time key display

### 📊 System Monitoring
- Real-time system statistics
- Performance metrics visualization
- Cache performance tracking
- Background task monitoring
- Error tracking

## 📋 Prerequisites

- Python 3.11 or higher
- RAG Pipeline API running on `http://localhost:8000`
- Required Python packages (see requirements-streamlit.txt)

## 🚀 Quick Start

### Method 1: Using Run Scripts

**Windows:**
```cmd
run.bat
```

**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

### Method 2: Manual Setup

1. **Install dependencies:**
```bash
pip install -r requirements-streamlit.txt
```

2. **Start the API (in another terminal):**
```bash
python -m uvicorn app.main:app --reload
```

3. **Start Streamlit UI:**
```bash
streamlit run streamlit_app.py
```

4. **Access the UI:**
   - Open http://localhost:8501 in your browser
   - API should be running on http://localhost:8000

## 🔧 Detailed Setup

### 1. Environment Setup

Create a virtual environment (recommended):
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements-streamlit.txt
```

Required packages:
- `streamlit>=1.28.0` - Main UI framework
- `requests>=2.31.0` - API communication
- `plotly>=5.15.0` - Interactive charts
- `pandas>=2.0.0` - Data manipulation

### 3. Configuration

The UI uses the following configuration files:

- `.streamlit/config.toml` - Streamlit configuration
- Environment variables (optional):
  - `API_BASE_URL` - API endpoint (default: http://localhost:8000)
  - `STREAMLIT_PORT` - UI port (default: 8501)

### 4. Start Services

**Start API first:**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0
```

**Start Streamlit UI:**
```bash
streamlit run streamlit_app.py
```

## 🐳 Docker Setup

### Build and Run with Docker Compose

1. **Start all services:**
```bash
docker-compose --profile ui up --build
```

2. **Start only UI and API:**
```bash
docker-compose up rag-app streamlit-ui --build
```

3. **Access services:**
   - Streamlit UI: http://localhost:8501
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Individual Docker Commands

**Build Streamlit image:**
```bash
docker build -f Dockerfile.streamlit -t rag-streamlit-ui .
```

**Run Streamlit container:**
```bash
docker run -p 8501:8501 \
  -e API_BASE_URL=http://host.docker.internal:8000 \
  rag-streamlit-ui
```

## 📖 Usage Guide

### 1. Authentication

**Registration:**
1. Open http://localhost:8501
2. Fill in the registration form (right side)
3. Username, email, and password required
4. Click "Register"

**Login:**
1. Use the login form (left side)
2. Enter your username and password
3. Click "Login"
4. You'll be redirected to the main dashboard

### 2. Document Management

**Upload Documents:**
1. Navigate to "📄 Document Manager"
2. Select PDF files using the file uploader
3. Choose sync or async processing
4. Click "🚀 Upload"
5. View upload results and any errors

**Manage Documents:**
1. View your uploaded documents
2. See metadata (pages, size, chunks)
3. Delete documents with confirmation
4. Refresh the list manually

### 3. Query Interface

**Ask Questions:**
1. Navigate to "🔍 Query Interface"
2. Enter your question in the text area
3. Configure search options:
   - Number of results (1-10)
   - Search type (hybrid/semantic/keyword)
   - Cache usage
4. Click "🚀 Ask Question"
5. View the answer and metadata

### 4. API Key Management

**Create API Keys:**
1. Navigate to "🔑 API Keys"
2. Enter a name for your key
3. Set expiration days (1-365)
4. Click "🔑 Create Key"
5. **Save the key immediately** (shown only once)

### 5. System Monitoring

**View Statistics:**
1. Navigate to "📊 Monitoring"
2. View system overview metrics
3. Check cache performance
4. Monitor background tasks
5. View performance charts

## ⚙️ API Configuration

The UI communicates with the RAG Pipeline API. Ensure the API is configured correctly:

### API Endpoints Used

- `GET /health` - Health check
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /upload` - File upload
- `POST /query` - Document queries
- `GET /documents` - List documents
- `DELETE /documents/{id}` - Delete document
- `GET /stats` - System statistics
- `POST /auth/api-keys` - Create API keys

### Required API Features

The UI requires these API features to be enabled:
- JWT authentication
- File upload with async processing
- Document management
- Query caching
- System monitoring
- API key management

## 🛠️ Troubleshooting

### Common Issues

**1. API Connection Failed**
```
🔴 API is not responding: Connection refused
```
**Solution:** Ensure the API is running on http://localhost:8000
```bash
python -m uvicorn app.main:app --reload
```

**2. Authentication Failed**
```
Login failed: 401 Unauthorized
```
**Solution:** 
- Check if user exists and password is correct
- Verify API authentication endpoints are working
- Clear browser cache/cookies

**3. File Upload Failed**
```
❌ Upload failed: 413 Request Entity Too Large
```
**Solution:**
- Check file size limits in API configuration
- Ensure files are valid PDFs
- Try uploading smaller files

**4. Missing Dependencies**
```
ModuleNotFoundError: No module named 'streamlit'
```
**Solution:**
```bash
pip install -r requirements-streamlit.txt
```

**5. Port Already in Use**
```
OSError: [Errno 48] Address already in use
```
**Solution:**
- Change port in `.streamlit/config.toml`
- Or kill existing process:
```bash
# Find process using port 8501
lsof -i :8501
kill -9 <PID>
```

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export STREAMLIT_LOG_LEVEL=debug
streamlit run streamlit_app.py
```

### Health Check

Run the test script to verify all components:
```bash
python test_streamlit.py
```

This will test:
- API connectivity
- User registration/login
- Document operations
- System statistics
- API key creation

### Performance Issues

**Slow Loading:**
- Check API response times
- Verify network connectivity
- Monitor system resources

**UI Responsiveness:**
- Refresh browser cache
- Check browser console for errors
- Ensure adequate system memory

## 📞 Support

If you encounter issues:

1. **Check the logs:**
   - Streamlit logs in terminal
   - API logs in `rag_pipeline.log`
   - Browser console for client-side errors

2. **Run the test script:**
   ```bash
   python test_streamlit.py
   ```

3. **Verify API health:**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Check configuration:**
   - `.streamlit/config.toml`
   - API environment variables
   - Port availability

## 🎯 Next Steps

Once the UI is running successfully:

1. **Create a user account** through the registration form
2. **Upload some PDF documents** to test the system
3. **Ask questions** about your documents
4. **Monitor system performance** through the dashboard
5. **Create API keys** for programmatic access

Enjoy using the RAG Pipeline Streamlit UI! 🚀
