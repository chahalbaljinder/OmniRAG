# PowerShell Setup Script for RAG Pipeline API
# Run this script to set up the development environment

Write-Host "🚀 Setting up RAG Pipeline API..." -ForegroundColor Green
Write-Host "=" * 50

# Check Python installation
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $pythonVersion detected" -ForegroundColor Green
    } else {
        Write-Host "❌ Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Create virtual environment (recommended)
$createVenv = Read-Host "Create a virtual environment? (y/n) [recommended: y]"
if ($createVenv -eq "y" -or $createVenv -eq "Y" -or $createVenv -eq "") {
    Write-Host "🔄 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Virtual environment created" -ForegroundColor Green
        Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
        .\venv\Scripts\Activate.ps1
    } else {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Install dependencies
Write-Host "🔄 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green

# Create necessary directories
$directories = @("uploads", "indexes", "faiss_index", "logs")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}
Write-Host "✅ Created necessary directories" -ForegroundColor Green

# Check .env file
if (!(Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "📝 Please create a .env file with your configuration." -ForegroundColor Yellow
    Write-Host "   Example .env content:" -ForegroundColor Yellow
    Write-Host "   GEMINI_API_KEY=your_api_key_here" -ForegroundColor Gray
    Write-Host "   SECRET_KEY=your_secret_key_here" -ForegroundColor Gray
    exit 1
} else {
    Write-Host "✅ .env file found" -ForegroundColor Green
}

# Initialize database
Write-Host "🔄 Initializing database..." -ForegroundColor Yellow
python -c "from app.database import init_db; init_db()"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Database initialized successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Database initialization may have failed, but continuing..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 To start the API server, run:" -ForegroundColor Cyan
Write-Host "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "📚 API Documentation will be available at:" -ForegroundColor Cyan
Write-Host "   http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 For enhanced features, use the v2 API at:" -ForegroundColor Cyan
Write-Host "   http://localhost:8000/api/v2/docs" -ForegroundColor Yellow
