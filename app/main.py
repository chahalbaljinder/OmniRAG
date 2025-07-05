import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv

# Import both API versions
from app.api import router as basic_api_router
from app.api_enhanced import router as enhanced_api_router
from app.async_processing import background_cleanup_task
from app.config import settings

# Load environment variables from .env file
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting RAG Pipeline API...")
    
    # Start background tasks
    cleanup_task = asyncio.create_task(background_cleanup_task())
    
    try:
        yield
    finally:
        # Shutdown
        print("🛑 Shutting down RAG Pipeline API...")
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title=settings.app_name,
    description="Advanced RAG Pipeline with Gemini 2.0 Flash - Upload documents and query them using LLMs with enhanced features.",
    version=settings.app_version,
    lifespan=lifespan,
    debug=settings.debug
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # In production, specify actual hosts
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(basic_api_router, prefix="/api/v1", tags=["Basic API"])
app.include_router(enhanced_api_router, prefix="/api/v2", tags=["Enhanced API"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🔍 RAG Pipeline API - Gemini 2.0 Flash Edition",
        "version": settings.app_version,
        "docs": "/docs",
        "basic_api": "/api/v1",
        "enhanced_api": "/api/v2",
        "features": [
            "Document Upload & Processing",
            "Semantic & Hybrid Search",
            "Authentication & Authorization",
            "Caching & Performance Monitoring",
            "Async Processing",
            "Advanced Analytics"
        ]
    }
