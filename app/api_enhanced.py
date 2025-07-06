# app/api_enhanced.py - Enhanced API with all advanced features

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request, Query as QueryParam
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import os
import shutil
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

# Import all our enhanced modules
from app.database import get_db, Document, Query, User, APIKey, create_tables
from app.auth import (
    get_current_user_or_api_key, get_current_user, require_admin,
    create_access_token, hash_password, verify_password, generate_api_key, hash_api_key,
    check_upload_rate_limit, check_query_rate_limit
)
from app.cache import cache_manager, embedding_cache, document_cache
from app.monitoring import performance_timer, log_to_database, performance_monitor, system_monitor, error_tracker
from app.search import hybrid_searcher, query_expander, reranker
from app.async_processing import task_manager, schedule_document_processing, schedule_complex_query
from app.security import SecurityValidator, validate_upload_files
from app.file_processor import DocumentProcessor
from app.embedding import create_faiss_index
from app.rag import get_answer
from app.utils import log_performance
from app.config import settings

# Create database tables
create_tables()

router = APIRouter()
security = HTTPBearer()

# Get project root and create directories
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ===================== AUTHENTICATION ENDPOINTS =====================

@router.post("/auth/register")
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already registered")
        
        # Create new user
        hashed_password = hash_password(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role="user"
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create access token
        access_token = create_access_token(user.id, user.username, user.role)
        
        log_to_database("INFO", f"New user registered: {username}", "AUTH", user.id)
        
        return {
            "message": "User registered successfully",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        error_tracker.track_error(e, {"endpoint": "register", "username": username})
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/auth/login")
async def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Login user and return access token"""
    try:
        # Find user
        user = db.query(User).filter(User.username == username).first()
        
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account is disabled")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create access token
        access_token = create_access_token(user.id, user.username, user.role)
        
        log_to_database("INFO", f"User logged in: {username}", "AUTH", user.id)
        
        return {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_tracker.track_error(e, {"endpoint": "login", "username": username})
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/auth/api-keys")
async def create_api_key(
    name: str = Form(...),
    expires_days: int = Form(30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key for the current user"""
    try:
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        api_key_record = APIKey(
            user_id=current_user.id,
            name=name,
            key_hash=key_hash,
            expires_at=expires_at
        )
        
        db.add(api_key_record)
        db.commit()
        
        log_to_database("INFO", f"API key created: {name}", "AUTH", current_user.id)
        
        return {
            "message": "API key created successfully",
            "api_key": api_key,  # Only returned once!
            "key_id": api_key_record.id,
            "name": name,
            "expires_at": expires_at.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        error_tracker.track_error(e, {"endpoint": "create_api_key", "user_id": current_user.id})
        raise HTTPException(status_code=500, detail="Failed to create API key")

# ===================== ENHANCED UPLOAD ENDPOINTS =====================

@router.post("/upload")
@performance_timer("UPLOAD")
async def upload_files(
    request: Request,
    files: List[UploadFile] = File(...),
    async_processing: bool = Form(False),
    current_user: Optional[User] = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(check_upload_rate_limit)
):
    """Enhanced file upload with authentication and async processing"""
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

                # Extract basic metadata first
                try:
                    _, pdf_metadata = DocumentProcessor.extract_text_from_pdf(file_path)
                    
                    # Create database record
                    document = Document(
                        filename=safe_filename,
                        file_path=file_path,
                        file_size=pdf_metadata.get("file_size", 0),
                        page_count=pdf_metadata.get("page_count", 0),
                        upload_date=datetime.utcnow(),
                        file_hash=file_hash,
                        metadata=json.dumps(pdf_metadata),
                        owner_id=current_user.id if current_user else None
                    )
                    
                    db.add(document)
                    db.flush()  # Get the document ID
                    
                    if async_processing:
                        # Schedule async processing
                        task_id = await schedule_document_processing(file_path, document.id)
                        
                        uploaded_documents.append({
                            "id": document.id,
                            "filename": safe_filename,
                            "task_id": task_id,
                            "status": "processing",
                            "pages": pdf_metadata.get("page_count", 0),
                            "file_size": pdf_metadata.get("file_size", 0)
                        })
                    else:
                        # Process synchronously
                        chunk_count = create_faiss_index(file_path, document.id)
                        document.chunk_count = chunk_count
                        
                        uploaded_documents.append({
                            "id": document.id,
                            "filename": safe_filename,
                            "chunks": chunk_count,
                            "pages": pdf_metadata.get("page_count", 0),
                            "file_size": pdf_metadata.get("file_size", 0),
                            "status": "completed"
                        })
                    
                    db.commit()

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
            "processing_time": round(duration, 3),
            "async_processing": async_processing
        }
        
        if processing_errors:
            response_data["errors"] = processing_errors
            
        return response_data

    except Exception as e:
        db.rollback()
        error_tracker.track_error(e, {"endpoint": "upload", "user_id": current_user.id if current_user else None})
        return JSONResponse(status_code=500, content={"error": f"Upload failed: {str(e)}"})

@router.get("/upload/status/{task_id}")
async def get_upload_status(
    task_id: str,
    current_user: Optional[User] = Depends(get_current_user_or_api_key)
):
    """Get status of async upload task"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task.to_dict()

# ===================== ENHANCED QUERY ENDPOINTS =====================

@router.post("/query")
@performance_timer("QUERY")
async def query_documents(
    request: Request,
    query: str = Form(...),
    k: int = Form(3),
    search_type: str = Form("hybrid"),  # hybrid, semantic, keyword
    use_cache: bool = Form(True),
    expand_query: bool = Form(True),
    async_processing: bool = Form(False),
    current_user: Optional[User] = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(check_query_rate_limit)
):
    """Enhanced document querying with advanced search options"""
    start_time = time.time()
    
    try:
        # Validate query
        if not SecurityValidator.validate_query(query):
            return JSONResponse(status_code=400, content={"error": "Invalid query format or content"})

        # Get accessible documents
        if current_user:
            documents = db.query(Document).filter(
                (Document.owner_id == current_user.id) | (Document.is_public == True)
            ).all()
        else:
            documents = db.query(Document).filter(Document.is_public == True).all()
        
        if not documents:
            return JSONResponse(status_code=400, content={"error": "No accessible documents found"})

        document_ids = [doc.id for doc in documents]
        
        # Check cache first
        cached_response = None
        if use_cache:
            cached_response = cache_manager.get_cached_response(query, document_ids, k, db)
        
        if cached_response:
            return {
                "query": query,
                "answer": cached_response,
                "documents_searched": len(documents),
                "processing_time": 0.001,
                "cached": True,
                "search_type": "cached"
            }
        
        if async_processing:
            # Schedule async processing
            task_id = await schedule_complex_query(query, document_ids, search_type)
            
            return {
                "query": query,
                "task_id": task_id,
                "status": "processing",
                "documents_to_search": len(documents),
                "search_type": search_type
            }
        
        # Process synchronously
        try:
            # Expand query if requested
            processed_query = query
            if expand_query:
                processed_query = query_expander.expand_query(query)
            
            # Get answer from RAG system
            doc_paths = [doc.file_path for doc in documents]
            answer = get_answer(processed_query, doc_paths, k=k)
            
            # Cache the response
            if use_cache:
                cache_manager.cache_response(query, answer, document_ids, k, db)
            
            # Log query to database
            query_record = Query(
                query_text=query,
                response_text=answer,
                processing_time=time.time() - start_time,
                documents_used=json.dumps(document_ids),
                timestamp=datetime.utcnow(),
                user_id=current_user.id if current_user else None,
                search_type=search_type
            )
            
            db.add(query_record)
            db.commit()
            
            duration = time.time() - start_time
            log_performance("QUERY_PROCESSING", duration, documents=len(documents))

            return {
                "query": query,
                "processed_query": processed_query if expand_query else None,
                "answer": answer,
                "documents_searched": len(documents),
                "processing_time": round(duration, 3),
                "query_id": query_record.id,
                "search_type": search_type,
                "cached": False
            }
            
        except Exception as e:
            error_tracker.track_error(e, {
                "endpoint": "query", 
                "user_id": current_user.id if current_user else None,
                "query": query[:100]
            })
            return JSONResponse(status_code=500, content={"error": f"Query processing failed: {str(e)}"})

    except Exception as e:
        error_tracker.track_error(e, {
            "endpoint": "query", 
            "user_id": current_user.id if current_user else None
        })
        return JSONResponse(status_code=500, content={"error": f"Query failed: {str(e)}"})

@router.get("/query/status/{task_id}")
async def get_query_status(
    task_id: str,
    current_user: Optional[User] = Depends(get_current_user_or_api_key)
):
    """Get status of async query task"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task.to_dict()

# ===================== DOCUMENT MANAGEMENT ENDPOINTS =====================

@router.get("/documents")
async def list_documents(
    skip: int = QueryParam(0),
    limit: int = QueryParam(100),
    owner_only: bool = QueryParam(False),
    current_user: Optional[User] = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """Enhanced document listing with pagination and filtering"""
    try:
        query = db.query(Document)
        
        # Filter by access permissions
        if current_user:
            if owner_only:
                query = query.filter(Document.owner_id == current_user.id)
            else:
                query = query.filter(
                    (Document.owner_id == current_user.id) | (Document.is_public == True)
                )
        else:
            query = query.filter(Document.is_public == True)
        
        # Apply pagination
        documents = query.order_by(Document.upload_date.desc()).offset(skip).limit(limit).all()
        total_count = query.count()
        
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
                "is_public": doc.is_public,
                "owner_id": doc.owner_id,
                "file_hash": doc.file_hash[:16] + "...",
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
            "total_count": total_count,
            "showing": len(document_list),
            "skip": skip,
            "limit": limit,
            "has_more": skip + len(document_list) < total_count
        }
        
    except Exception as e:
        error_tracker.track_error(e, {"endpoint": "list_documents"})
        return JSONResponse(status_code=500, content={"error": f"Failed to list documents: {str(e)}"})

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document (owner or admin only)"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check permissions
        if current_user.role != "admin" and document.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this document")
        
        # Remove file
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Remove from database
        db.delete(document)
        db.commit()
        
        # Invalidate cache
        cache_manager.invalidate_document_cache([document_id], db)
        
        log_to_database("INFO", f"Document deleted: {document.filename}", "DOCUMENT", current_user.id)
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        error_tracker.track_error(e, {"endpoint": "delete_document", "document_id": document_id})
        raise HTTPException(status_code=500, detail="Failed to delete document")

# ===================== ADMIN ENDPOINTS =====================

@router.get("/admin/users")
async def list_users(
    skip: int = QueryParam(0),
    limit: int = QueryParam(100),
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        total_count = db.query(User).count()
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "document_count": len(user.documents),
                "query_count": len(user.queries)
            })
        
        return {
            "users": user_list,
            "total_count": total_count,
            "showing": len(user_list)
        }
        
    except Exception as e:
        error_tracker.track_error(e, {"endpoint": "list_users"})
        raise HTTPException(status_code=500, detail="Failed to list users")

@router.get("/admin/system-logs")
async def get_system_logs(
    skip: int = QueryParam(0),
    limit: int = QueryParam(100),
    level: Optional[str] = QueryParam(None),
    component: Optional[str] = QueryParam(None),
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Get system logs (admin only)"""
    try:
        from app.database import SystemLog
        
        query = db.query(SystemLog)
        
        if level:
            query = query.filter(SystemLog.level == level)
        
        if component:
            query = query.filter(SystemLog.component == component)
        
        logs = query.order_by(SystemLog.timestamp.desc()).offset(skip).limit(limit).all()
        total_count = query.count()
        
        log_list = []
        for log in logs:
            log_data = {
                "id": log.id,
                "level": log.level,
                "message": log.message,
                "timestamp": log.timestamp.isoformat(),
                "component": log.component,
                "user_id": log.user_id
            }
            
            if log.log_metadata:
                try:
                    log_data["metadata"] = json.loads(log.log_metadata)
                except:
                    log_data["metadata"] = {}
            
            log_list.append(log_data)
        
        return {
            "logs": log_list,
            "total_count": total_count,
            "showing": len(log_list)
        }
        
    except Exception as e:
        error_tracker.track_error(e, {"endpoint": "system_logs"})
        raise HTTPException(status_code=500, detail="Failed to get system logs")

# ===================== MONITORING ENDPOINTS =====================

@router.get("/health")
async def health_check():
    """Comprehensive health check"""
    return system_monitor.health_check()

@router.get("/stats")
async def get_statistics(
    current_user: Optional[User] = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """Get comprehensive system statistics"""
    try:
        # Basic stats
        if current_user:
            documents = db.query(Document).filter(
                (Document.owner_id == current_user.id) | (Document.is_public == True)
            ).all()
            queries = db.query(Query).filter(Query.user_id == current_user.id).all()
        else:
            documents = db.query(Document).filter(Document.is_public == True).all()
            queries = []
        
        # Performance metrics
        perf_stats = {}
        for metric_name in performance_monitor.metrics:
            perf_stats[metric_name] = performance_monitor.get_statistics(metric_name)
        
        # Cache stats
        cache_stats = cache_manager.get_cache_stats(db)
        embedding_cache_stats = embedding_cache.stats()
        document_cache_stats = document_cache.stats()
        
        # Task stats
        all_tasks = task_manager.get_all_tasks()
        task_stats = {
            "total": len(all_tasks),
            "pending": len([t for t in all_tasks if t.status.value == "pending"]),
            "running": len([t for t in all_tasks if t.status.value == "running"]),
            "completed": len([t for t in all_tasks if t.status.value == "completed"]),
            "failed": len([t for t in all_tasks if t.status.value == "failed"])
        }
        
        # Error stats
        error_stats = error_tracker.get_error_summary()
        
        return {
            "documents": {
                "accessible": len(documents),
                "total_pages": sum(doc.page_count for doc in documents),
                "total_chunks": sum(doc.chunk_count for doc in documents),
                "total_size_bytes": sum(doc.file_size for doc in documents)
            },
            "queries": {
                "total": len(queries),
                "average_processing_time": sum(q.processing_time for q in queries) / len(queries) if queries else 0
            },
            "performance": perf_stats,
            "cache": {
                "query_cache": cache_stats,
                "embedding_cache": embedding_cache_stats,
                "document_cache": document_cache_stats
            },
            "tasks": task_stats,
            "errors": error_stats,
            "system": system_monitor.get_system_stats()
        }
        
    except Exception as e:
        error_tracker.track_error(e, {"endpoint": "stats"})
        return JSONResponse(status_code=500, content={"error": f"Failed to get statistics: {str(e)}"})

@router.get("/performance-metrics")
async def get_performance_metrics(
    metric_name: Optional[str] = QueryParam(None),
    current_user: User = Depends(require_admin())
):
    """Get detailed performance metrics (admin only)"""
    try:
        if metric_name:
            return {
                "metric_name": metric_name,
                "data": performance_monitor.get_metrics(metric_name),
                "statistics": performance_monitor.get_statistics(metric_name)
            }
        else:
            all_metrics = {}
            for name in performance_monitor.metrics:
                all_metrics[name] = performance_monitor.get_statistics(name)
            
            return {
                "all_metrics": all_metrics,
                "available_metrics": list(performance_monitor.metrics.keys())
            }
    
    except Exception as e:
        error_tracker.track_error(e, {"endpoint": "performance_metrics"})
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")
