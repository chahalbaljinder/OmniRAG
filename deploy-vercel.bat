@echo off
echo 🚀 Deploying RAG Pipeline to Vercel...

REM Check if vercel CLI is installed
where vercel >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Vercel CLI not found. Installing...
    npm install -g vercel
)

REM Check if logged in
vercel whoami >nul 2>nul
if %errorlevel% neq 0 (
    echo 🔑 Please login to Vercel
    vercel login
)

echo 📡 Deploying backend...

REM Deploy backend first
vercel --prod --yes

echo ✅ Backend deployed!

REM Deploy frontend
echo 🎨 Deploying frontend...
cd frontend

REM Deploy frontend
vercel --prod --yes

cd ..

echo ✅ Frontend deployed!
echo.
echo 🌐 Your RAG Pipeline is now live on Vercel!
echo 📚 Check your Vercel dashboard for URLs
echo ⚙️  Don't forget to set environment variables:
echo    - Backend: GEMINI_API_KEY, DATABASE_URL, SECRET_KEY, etc.
echo    - Frontend: REACT_APP_API_URL
echo.
echo 📖 See VERCEL_DEPLOYMENT.md for detailed instructions

pause
