@echo off
REM Deployment script for RAG Pipeline on Windows

echo 🚀 Starting RAG Pipeline Deployment...

REM Check if .env file exists
if not exist .env (
    echo ⚠️  .env file not found. Creating from template...
    copy .env.docker .env
    echo ✅ Please edit .env file with your configuration before continuing.
    pause
    exit /b 1
)

REM Build and start services
echo 🔨 Building Docker images...
docker-compose build

echo 🏃 Starting services...
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak > nul

REM Check health
echo 🏥 Checking application health...
set max_attempts=30
set attempt=1

:health_check
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Application is healthy!
    goto :success
)

if %attempt% geq %max_attempts% (
    echo ❌ Application failed to start properly
    docker-compose logs rag-app
    pause
    exit /b 1
)

echo Attempt %attempt%/%max_attempts% - waiting for application...
timeout /t 5 /nobreak > nul
set /a attempt+=1
goto :health_check

:success
echo 🎉 RAG Pipeline deployed successfully!
echo 📖 API Documentation: http://localhost:8000/docs
echo 🔍 Application: http://localhost:8000
echo 📊 Health Check: http://localhost:8000/health

REM Show running containers
echo 📦 Running containers:
docker-compose ps

pause
