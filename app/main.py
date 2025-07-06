import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
from fastapi import Form, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
from fastapi import File, UploadFile

# Import both API versions
from app.api import router as basic_api_router
from app.api_enhanced import router as enhanced_api_router
from app.async_processing import background_cleanup_task
from app.config import settings
from app.auth import authenticate_user, create_access_token, get_password_hash, get_current_active_user
from app.database import get_db, User

# Load environment variables from .env file
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting RAG Pipeline API...")
    
    # Initialize database
    from app.database import init_db
    init_db()
    
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

# Add core routes directly to main app (without v1 prefix)
@app.post("/upload")
async def upload_files_main(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Main upload endpoint - delegates to v1 upload"""
    # Import here to avoid circular imports
    from app.api import upload_files
    return await upload_files(files, db)

@app.post("/query")
async def query_documents_main(query: str = Form(...), k: int = Form(3), db: Session = Depends(get_db)):
    """Main query endpoint - delegates to v1 query"""
    # Import here to avoid circular imports
    from app.api import query_documents
    return await query_documents(query, k, db)

@app.get("/documents")
async def list_documents_main(db: Session = Depends(get_db)):
    """Main documents list endpoint - delegates to v1 documents"""
    # Import here to avoid circular imports
    from app.api import list_documents
    return await list_documents(db)

@app.get("/document/{document_id}")
async def get_document_details_main(document_id: int, db: Session = Depends(get_db)):
    """Main document details endpoint - delegates to v1 document details"""
    # Import here to avoid circular imports
    from app.api import get_document_details
    return await get_document_details(document_id, db)

# Add missing monitoring routes to main app (without prefix)
@app.get("/health")
async def health_check_main(db: Session = Depends(get_db)):
    """Main health check endpoint - delegates to v1 health"""
    # Import here to avoid circular imports
    from app.api import health_check
    return await health_check(db)

@app.get("/stats")
async def stats_main(db: Session = Depends(get_db)):
    """Main stats endpoint - delegates to v1 stats"""
    # Import here to avoid circular imports
    from app.api import get_statistics
    return await get_statistics(db)

@app.get("/admin/monitoring")
async def admin_monitoring_main():
    """Admin monitoring dashboard endpoint"""
    # This should require admin access, return 401 for unauthorized
    from fastapi import HTTPException
    raise HTTPException(status_code=401, detail="Admin access required")

# Add authentication routes directly to the main app (not v1 router)
@app.post("/auth/register")
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """User registration endpoint"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Check if email already exists  
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash the password
        hashed_password = get_password_hash(password)
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            role="user"
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "message": "User registered successfully",
            "user_id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/auth/login")
async def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """User login endpoint"""
    try:
        user = authenticate_user(username, password, db)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")
        
        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            user_id=user.id, 
            username=user.username, 
            role=user.role
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/auth/me")
async def get_current_user_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }

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
