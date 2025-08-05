# RAG Pipeline Frontend Deployment Guide

## Free Tier Deployment Options

### 1. Netlify (Recommended)
- **Free Tier**: 100GB bandwidth, 300 build minutes/month
- **Auto-deploys** from Git repositories
- **Custom domains** supported

#### Setup:
1. Connect your GitHub repository to Netlify
2. Set build command: `npm run build:prod`
3. Set publish directory: `build`
4. Add environment variable: `REACT_APP_API_URL=your-api-url`

### 2. Vercel
- **Free Tier**: 100GB bandwidth, unlimited personal projects
- **Excellent performance** with edge caching
- **Automatic HTTPS**

#### Setup:
1. Import project from GitHub
2. Framework preset: Create React App
3. Build command: `npm run build:prod`
4. Output directory: `build`
5. Add environment variable: `REACT_APP_API_URL=your-api-url`

### 3. GitHub Pages
- **Completely free** for public repositories
- **Custom domains** supported
- **GitHub Actions** for automated deployment

#### Setup:
1. Enable GitHub Pages in repository settings
2. Use the included `.github/workflows/deploy.yml`
3. Add repository secret: `REACT_APP_API_URL`

### 4. Firebase Hosting
- **Free Tier**: 10GB storage, 125K reads/month
- **Global CDN** and SSL certificates
- **Easy CLI** deployment

#### Setup:
```bash
cd frontend
npm install -g firebase-tools
firebase login
firebase init hosting
npm run build:prod
firebase deploy
```

## Environment Configuration

### Required Environment Variables:
- `REACT_APP_API_URL`: Your backend API URL
- `CI=false`: Prevents build failures from warnings
- `GENERATE_SOURCEMAP=false`: Reduces build size

### File Structure:
```
frontend/
├── .env.example          # Environment template
├── netlify.toml          # Netlify configuration
├── vercel.json           # Vercel configuration
└── .github/workflows/    # GitHub Actions
```

## Build Optimization

### Production Build Features:
- **Tree shaking** for smaller bundles
- **Code splitting** for faster loading
- **Asset optimization** with caching headers
- **Error handling** for better UX

### Commands:
```bash
# Development
npm start

# Production build
npm run build:prod

# Local production test
npm run serve
```

## API Backend Deployment

### Free Backend Options:
1. **Railway** - 500 hours/month free
2. **Render** - 750 hours/month free  
3. **Heroku alternatives** - Fly.io, Railway
4. **Supabase** - PostgreSQL + Edge Functions

### CORS Configuration:
Ensure your API allows requests from your frontend domain:

```python
# FastAPI example
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Security Considerations

### Headers (included in configurations):
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Environment Variables:
- Never commit `.env` files
- Use platform-specific secret management
- Prefix React variables with `REACT_APP_`

## Monitoring and Analytics

### Free Options:
- **Google Analytics** - Web analytics
- **Sentry** - Error tracking (free tier)
- **LogRocket** - Session replay (free tier)
- **Hotjar** - User behavior (free tier)

## Custom Domain Setup

1. **Purchase domain** from Namecheap, Google Domains, etc.
2. **Add CNAME record** pointing to your hosting provider
3. **Configure SSL** (usually automatic)
4. **Update CORS** settings in your API

## Troubleshooting

### Common Issues:
1. **Build failures**: Check Node.js version (use 16+)
2. **API connection**: Verify CORS and environment variables
3. **Routing issues**: Ensure SPA redirect rules are configured
4. **Performance**: Enable gzip compression and caching

### Debug Commands:
```bash
# Check build locally
npm run build:prod
npm run serve

# Environment variables
echo $REACT_APP_API_URL

# Network debugging
curl -I https://your-api-url/health
```
