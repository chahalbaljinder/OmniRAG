#!/bin/bash

echo "🚀 Deploying RAG Pipeline to Vercel..."

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if logged in
if ! vercel whoami &> /dev/null; then
    echo "🔑 Please login to Vercel"
    vercel login
fi

echo "📡 Deploying backend..."

# Deploy backend first
vercel --prod --yes

echo "✅ Backend deployed!"

# Deploy frontend
echo "🎨 Deploying frontend..."
cd frontend

# Deploy frontend
vercel --prod --yes

cd ..

echo "✅ Frontend deployed!"
echo ""
echo "🌐 Your RAG Pipeline is now live on Vercel!"
echo "📚 Check your Vercel dashboard for URLs"
echo "⚙️  Don't forget to set environment variables:"
echo "   - Backend: GEMINI_API_KEY, DATABASE_URL, SECRET_KEY, etc."
echo "   - Frontend: REACT_APP_API_URL"
echo ""
echo "📖 See VERCEL_DEPLOYMENT.md for detailed instructions"
