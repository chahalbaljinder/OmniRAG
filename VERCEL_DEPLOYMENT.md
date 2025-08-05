# Vercel Deployment Guide

## Prerequisites

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

## Backend Deployment

### 1. Deploy Backend API

```bash
# From the root directory
vercel --prod
```

**If you encounter issues with the current vercel.json, try the alternative:**
```bash
# Backup current config
mv vercel.json vercel-builds.json

# Use the alternative config
mv vercel-alternative.json vercel.json

# Deploy again
vercel --prod
```

### 2. Set Environment Variables

After the first deployment, set the required environment variables:

```bash
vercel env add GEMINI_API_KEY
# Enter your Gemini API key when prompted

vercel env add DATABASE_URL
# Enter: sqlite:///tmp/rag_pipeline.db

vercel env add REDIS_URL  
# Enter: redis://localhost:6379/0 (or use Vercel KV)

vercel env add REDIS_ENABLED
# Enter: false (for now, or true if using Vercel KV)

vercel env add SECRET_KEY
# Enter a secure random string (generate with: openssl rand -hex 32)

vercel env add ALGORITHM
# Enter: HS256

vercel env add ACCESS_TOKEN_EXPIRE_MINUTES
# Enter: 30

vercel env add ENABLE_CACHING
# Enter: true

vercel env add CACHE_TTL
# Enter: 3600

vercel env add MAX_CHUNK_SIZE
# Enter: 800

vercel env add OVERLAP_SIZE
# Enter: 150

vercel env add LOG_LEVEL
# Enter: INFO
```

### 3. Redeploy Backend
```bash
vercel --prod
```

## Frontend Deployment

### 1. Navigate to Frontend Directory
```bash
cd frontend
```

### 2. Deploy Frontend
```bash
vercel --prod
```

### 3. Set Frontend Environment Variables
```bash
vercel env add REACT_APP_API_URL
# Enter your backend API URL (e.g., https://your-backend.vercel.app)
```

### 4. Redeploy Frontend
```bash
vercel --prod
```

## Complete Deployment Script

Create this script to deploy both:

```bash
#!/bin/bash

echo "🚀 Deploying RAG Pipeline to Vercel..."

# Deploy backend
echo "📡 Deploying backend..."
vercel --prod --yes

# Get backend URL
BACKEND_URL=$(vercel ls --scope=your-team | grep rag-pipeline | head -1 | awk '{print $2}')
echo "✅ Backend deployed to: https://$BACKEND_URL"

# Deploy frontend
echo "🎨 Deploying frontend..."
cd frontend

# Set the API URL environment variable
vercel env add REACT_APP_API_URL production "https://$BACKEND_URL"

# Deploy frontend
vercel --prod --yes

echo "✅ Deployment complete!"
echo "🌐 Your app is now live!"
```

## Configuration Files

### Backend (`vercel.json`)
- Configures Python serverless functions
- Sets up routing for FastAPI endpoints
- Defines environment variables
- Sets function timeout to 30 seconds

### Frontend (`frontend/vercel.json`)
- Configures React build settings
- Sets up SPA routing
- Enables static asset caching
- Disables source maps for production

## Environment Variables Summary

### Backend Variables:
- `GEMINI_API_KEY` - Your Google Gemini API key
- `DATABASE_URL` - SQLite database path
- `SECRET_KEY` - JWT secret key
- `REDIS_ENABLED` - Enable/disable caching
- Other configuration variables

### Frontend Variables:
- `REACT_APP_API_URL` - Backend API URL

## Vercel Features Used

### Backend:
- **Serverless Functions** - Auto-scaling Python functions
- **Environment Variables** - Secure configuration
- **Custom Domains** - Professional URLs
- **Analytics** - Performance monitoring

### Frontend:
- **Static Site Hosting** - Fast CDN delivery
- **SPA Support** - Client-side routing
- **Build Optimization** - Automatic minification
- **Preview Deployments** - Branch previews

## Troubleshooting

### Common Issues:

1. **Cold Start Delays**
   - First request may be slow due to serverless cold start
   - Consider upgrading to Pro for faster cold starts

2. **Function Timeout**
   - Current limit: 30 seconds (free tier)
   - Optimize large file uploads or consider Pro plan

3. **Database Persistence**
   - SQLite files are ephemeral on Vercel
   - Consider upgrading to PostgreSQL with Vercel Postgres

4. **CORS Issues**
   - Ensure frontend URL is in CORS origins
   - Check environment variables are set correctly

### Useful Commands:

```bash
# Check deployment status
vercel ls

# View logs
vercel logs [deployment-url]

# Remove deployment
vercel rm [deployment-name]

# View environment variables
vercel env ls

# Pull environment variables locally
vercel env pull
```

## Production Recommendations

1. **Database**: Upgrade to Vercel Postgres for persistence
2. **Caching**: Use Vercel KV for Redis caching
3. **Storage**: Use Vercel Blob for file uploads
4. **Monitoring**: Enable Vercel Analytics
5. **Custom Domain**: Add your own domain
6. **Team Plan**: For better performance and features

## Cost Optimization

### Free Tier Limits:
- **Serverless Functions**: 100GB-hours
- **Bandwidth**: 100GB
- **Build Execution**: 6,000 minutes

### Tips:
- Optimize bundle sizes
- Use caching effectively
- Monitor usage in Vercel dashboard
- Consider upgrading for production workloads
