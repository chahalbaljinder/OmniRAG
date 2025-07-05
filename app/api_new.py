# app/api.py - Enhanced API with database integration and security

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
import os
import shutil
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.embedding import create_faiss_index
from app.rag import get_answer
from app.security import SecurityValidator, validate_upload_files
from app.file_processor import DocumentProcessor
from app.database import get_db, Document, Query, create_tables
from app.utils import log_performance

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
            metadata = json.loads(doc.metadata) if doc.metadata else {}
            
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
