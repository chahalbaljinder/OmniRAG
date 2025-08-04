from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List
from fastapi import File, UploadFile

# Import basic API only
from app.api import router as basic_api_router
from app.config import settings

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title=settings.app_name,
    description="Basic RAG Pipeline - Upload documents and query them using LLMs",
    version=settings.app_version,
    debug=settings.debug
)

# Add security middleware (removed TrustedHostMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include basic API routes only
app.include_router(basic_api_router, tags=["Basic API"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🔍 Basic RAG Pipeline API",
        "version": settings.app_version,
        "docs": "/docs",
        "features": [
            "Document Upload & Processing",
            "Basic Query & RAG",
            "Document Management",
            "Health Monitoring"
        ]
    }
