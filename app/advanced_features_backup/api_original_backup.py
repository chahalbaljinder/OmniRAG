# app/api.py - Enhanced API with database integration and security

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
import os
import shutil
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.embedding import create_faiss_index
from app.rag import get_answer
from app.security import SecurityValidator, validate_upload_files
from app.file_processor import DocumentProcessor
from app.database import get_db, Document, Query, User, Task, create_tables
from app.utils import log_performance
from app.auth import (
    get_current_user, get_current_active_user, require_admin,
    authenticate_user, create_access_token, get_password_hash,
    check_upload_rate_limit, check_query_rate_limit
)
from app.cache import query_cache, get_cache_stats, clear_all_cache
from app.monitoring import (
    monitor_operation, get_monitoring_dashboard, 
    log_security_event, monitor_performance
)
try:
    from app.hybrid_search import search_documents, initialize_hybrid_search
    HYBRID_SEARCH_AVAILABLE = True
except ImportError:
    HYBRID_SEARCH_AVAILABLE = False
    
try:
    from app.async_processing import (
        submit_async_task, get_task_status, cancel_task, 
        get_all_tasks, cleanup_old_tasks
    )
    ASYNC_PROCESSING_AVAILABLE = True
except ImportError:
    ASYNC_PROCESSING_AVAILABLE = False

# Create database tables
create_tables()

router = APIRouter()

# Get project root and create uploads directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Enhanced file upload with validation and database integration"""
    start_time = time.time()
    
    try:
        # Validate files
        validation_errors = validate_upload_files(files)
        if validation_errors:
            return JSONResponse(status_code=400, content={"errors": validation_errors})

        uploaded_documents = []
        processing_errors = []

        for file in files:
            try:
                # Sanitize filename
                safe_filename = SecurityValidator.sanitize_filename(file.filename)
                file_path = os.path.join(UPLOAD_DIR, safe_filename)
                
                # Read file content for hash calculation
                file_content = await file.read()
                file_hash = SecurityValidator.calculate_file_hash(file_content)
                
                # Check for duplicate files
                existing_doc = db.query(Document).filter(Document.file_hash == file_hash).first()
                if existing_doc:
                    processing_errors.append(f"File {file.filename} already exists (duplicate content)")
                    continue
                
                # Save file
                with open(file_path, "wb") as buffer:
                    buffer.write(file_content)

                # Process document and extract metadata
                try:
                    text, pdf_metadata = DocumentProcessor.extract_text_from_pdf(file_path)
                    validation_result = DocumentProcessor.validate_document_content(text, pdf_metadata)
                    
                    # Create database record
                    document = Document(
                        filename=safe_filename,
                        file_path=file_path,
                        file_size=pdf_metadata.get("file_size", 0),
                        page_count=pdf_metadata.get("page_count", 0),
                        upload_date=datetime.utcnow(),
                        file_hash=file_hash,
                        metadata=json.dumps(pdf_metadata)
                    )
                    
                    db.add(document)
                    db.flush()  # Get the document ID
                    
                    # Create FAISS index
                    chunk_count = create_faiss_index(file_path, document.id)
                    
                    # Update chunk count
                    document.chunk_count = chunk_count
                    db.commit()

                    uploaded_documents.append({
                        "id": document.id,
                        "filename": safe_filename,
                        "chunks": chunk_count,
                        "pages": pdf_metadata.get("page_count", 0),
                        "file_size": pdf_metadata.get("file_size", 0),
                        "warnings": validation_result.get("warnings", [])
                    })

                except Exception as e:
                    db.rollback()
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    processing_errors.append(f"Failed to process {file.filename}: {str(e)}")

            except Exception as e:
                processing_errors.append(f"Failed to upload {file.filename}: {str(e)}")

        duration = time.time() - start_time
        log_performance("FILE_UPLOAD", duration, files=len(files), successful=len(uploaded_documents))

        response_data = {
            "status": "completed",
            "uploaded": uploaded_documents,
            "total_uploaded": len(uploaded_documents),
            "processing_time": round(duration, 3)
        }
        
        if processing_errors:
            response_data["errors"] = processing_errors
            
        return response_data

    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": f"Upload failed: {str(e)}"})

@router.post("/query")
async def query_documents(query: str = Form(...), k: int = Form(3), db: Session = Depends(get_db)):
    """Enhanced document querying with database logging"""
    start_time = time.time()
    
    try:
        # Validate query
        if not SecurityValidator.validate_query(query):
            return JSONResponse(status_code=400, content={"error": "Invalid query format or content"})

        # Get all documents from database
        documents = db.query(Document).all()
        
        if not documents:
            return JSONResponse(status_code=400, content={"error": "No documents uploaded yet."})

        # Prepare document paths
        doc_paths = [doc.file_path for doc in documents]
        
        try:
            # Get answer from RAG system
            answer = get_answer(query, doc_paths, k=k)
            
            # Log query to database
            query_record = Query(
                query_text=query,
                response_text=answer,
                processing_time=time.time() - start_time,
                documents_used=json.dumps([doc.id for doc in documents]),
                timestamp=datetime.utcnow()
            )
            
            db.add(query_record)
            db.commit()
            
            duration = time.time() - start_time
            log_performance("QUERY_PROCESSING", duration, documents=len(documents))

            return {
                "query": query,
                "answer": answer,
                "documents_searched": len(documents),
                "processing_time": round(duration, 3),
                "query_id": query_record.id
            }
            
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": f"Query processing failed: {str(e)}"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Query failed: {str(e)}"})

@router.get("/documents")
async def list_documents(db: Session = Depends(get_db)):
    """Enhanced document listing with comprehensive metadata"""
    try:
        documents = db.query(Document).order_by(Document.upload_date.desc()).all()
        
        document_list = []
        for doc in documents:
            metadata = json.loads(doc.file_metadata) if doc.file_metadata else {}
            
            document_list.append({
                "id": doc.id,
                "filename": doc.filename,
                "upload_date": doc.upload_date.isoformat(),
                "file_size": doc.file_size,
                "page_count": doc.page_count,
                "chunk_count": doc.chunk_count,
                "file_hash": doc.file_hash[:16] + "...",  # Truncated hash for security
                "metadata": {
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "creation_date": metadata.get("creation_date", ""),
                    "extractable_pages": metadata.get("extractable_pages", 0),
                    "total_text_length": metadata.get("total_text_length", 0)
                }
            })
        
        return {
            "documents": document_list,
            "total_count": len(document_list),
            "total_pages": sum(doc["page_count"] for doc in document_list),
            "total_chunks": sum(doc["chunk_count"] for doc in document_list)
        }
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to list documents: {str(e)}"})

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database connection
        document_count = db.query(Document).count()
        
        # Check if uploads directory exists
        uploads_exist = os.path.exists(UPLOAD_DIR)
        
        # Check if indexes directory exists
        indexes_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "indexes")
        indexes_exist = os.path.exists(indexes_dir)
        
        return {
            "status": "healthy",
            "database_connected": True,
            "uploads_directory": uploads_exist,
            "indexes_directory": indexes_exist,
            "total_documents": document_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(status_code=503, content={
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

@router.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """Get system statistics"""
    try:
        documents = db.query(Document).all()
        queries = db.query(Query).all()
        
        return {
            "documents": {
                "total": len(documents),
                "total_pages": sum(doc.page_count for doc in documents),
                "total_chunks": sum(doc.chunk_count for doc in documents),
                "total_size_bytes": sum(doc.file_size for doc in documents)
            },
            "queries": {
                "total": len(queries),
                "average_processing_time": sum(q.processing_time for q in queries) / len(queries) if queries else 0
            },
            "system": {
                "uploads_directory": UPLOAD_DIR,
                "indexes_directory": os.path.join(PROJECT_ROOT, "indexes")
            }
        }
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to get statistics: {str(e)}"})

@router.post("/auth/register")
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
            "username": new_user.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/auth/login")
async def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """User login endpoint"""
    try:
        user = authenticate_user(db, username, password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")
        
        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role}, 
            expires_delta=access_token_expires
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

@router.get("/auth/me")
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

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Token login endpoint"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Check if the user is active
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
async def read_users_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user

@router.get("/users")
async def read_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of users (admin only)"""
    users = db.query(User).all()
    return users

@router.post("/users")
async def create_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new user (admin only)"""
    # Check if the current user is an admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Hash the password
    hashed_password = get_password_hash(password)
    
    # Create new user record
    new_user = User(
        username=username,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.put("/users/me")
async def update_user(
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update current user information"""
    if username:
        current_user.username = username
    if password:
        current_user.hashed_password = get_password_hash(password)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.post("/tasks/submit")
async def submit_task(
    background_tasks: BackgroundTasks,
    query: str = Form(...),
    k: int = Form(3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit a new task for processing"""
    task = {
        "query": query,
        "k": k,
        "user_id": current_user.id,
        "status": "pending",
        "result": None,
        "error": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Add task to database
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Submit task to background processor
    background_tasks.add_task(process_query_task, task.id)
    
    return {"task_id": task.id, "status": "submitted"}

@router.get("/tasks/{task_id}")
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get task status and result"""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task

@router.get("/tasks")
async def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all tasks for the current user"""
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    return tasks

@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a task"""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    
    return {"detail": "Task deleted"}

@router.post("/search")
async def search(
    query: str = Form(...),
    k: int = Form(3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Search documents using hybrid search"""
    if not HYBRID_SEARCH_AVAILABLE:
        raise HTTPException(status_code=501, detail="Hybrid search not available")
    
    # Perform hybrid search
    results = search_documents(query, k=k)
    
    return {
        "query": query,
        "results": results
    }

@router.get("/cache/stats")
async def cache_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get cache statistics"""
    stats = get_cache_stats()
    return stats

@router.post("/cache/clear")
async def cache_clear(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Clear all cache"""
    clear_all_cache()
    return {"detail": "Cache cleared"}

@router.get("/monitoring/dashboard")
async def monitoring_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get monitoring dashboard data"""
    dashboard_data = get_monitoring_dashboard()
    return dashboard_data

@router.post("/monitoring/log_security_event")
async def log_security(
    event_type: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Log a security event"""
    log_security_event(event_type, description)
    return {"detail": "Security event logged"}

@router.post("/monitoring/monitor_performance")
async def monitor_perf(
    operation_name: str = Form(...),
    duration_ms: float = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Monitor performance of an operation"""
    monitor_performance(operation_name, duration_ms)
    return {"detail": "Performance monitored"}

@router.get("/document/{document_id}")
async def get_document_details(document_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific document"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        metadata = json.loads(document.file_metadata) if document.file_metadata else {}
        
        return {
            "id": document.id,
            "filename": document.filename,
            "upload_date": document.upload_date.isoformat(),
            "file_size": document.file_size,
            "page_count": document.page_count,
            "chunk_count": document.chunk_count,
            "file_hash": document.file_hash,
            "metadata": metadata,
            "owner_id": getattr(document, 'owner_id', None)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document details: {str(e)}")

# Background task functions
def process_query_task(task_id: str, query: str, document_paths: List[str], k: int = 3):
    """Background task for processing queries"""
    from app.rag import get_answer
    from app.database import SessionLocal, Task
    
    db = SessionLocal()
    try:
        # Update task status
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.state = "running"
            task.started_at = datetime.utcnow()
            task.progress = 10.0
            db.commit()
        
        # Process query
        answer = get_answer(query, document_paths, k=k)
        
        # Update task with result
        if task:
            task.result = json.dumps({"answer": answer})
            task.state = "completed"
            task.completed_at = datetime.utcnow()
            task.progress = 100.0
            db.commit()
            
    except Exception as e:
        if task:
            task.error_message = str(e)
            task.state = "failed"
            task.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()

@router.on_event("startup")
async def startup_event():
    """Application startup event"""
    # Initialize hybrid search if available
    if HYBRID_SEARCH_AVAILABLE:
        initialize_hybrid_search()
    
    # Cleanup old tasks
    if ASYNC_PROCESSING_AVAILABLE:
        cleanup_old_tasks()

@router.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    pass
