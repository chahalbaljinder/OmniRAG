# app/api_basic.py - Simplified Basic API with minimal features

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import shutil
import time
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.embedding import create_faiss_index
from app.rag import get_answer
from app.file_processor import DocumentProcessor
from app.database import get_db, Document, Query, create_tables
from app.config import settings

# Create database tables
create_tables()

router = APIRouter()

# Get project root and create uploads directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Basic file upload endpoint"""
    uploaded_documents = []
    processing_errors = []

    for file in files:
        try:
            # Basic validation
            if not file.filename.endswith('.pdf'):
                processing_errors.append(f"File {file.filename} is not a PDF")
                continue
            
            # Save file
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Process document
            try:
                text, pdf_metadata = DocumentProcessor.extract_text_from_pdf(file_path)
                
                # Create database record
                document = Document(
                    filename=file.filename,
                    file_path=file_path,
                    file_size=pdf_metadata.get("file_size", 0),
                    page_count=pdf_metadata.get("page_count", 0),
                    upload_date=datetime.utcnow(),
                    content=text,
                    file_hash=f"hash_{int(time.time())}"  # Simple hash
                )
                
                db.add(document)
                db.commit()
                db.refresh(document)

                # Create FAISS index
                try:
                    create_faiss_index(file_path, document.id)
                    upload_status = "success"
                    error_message = None
                except Exception as e:
                    upload_status = "index_failed"
                    error_message = str(e)

                uploaded_documents.append({
                    "id": document.id,
                    "filename": document.filename,
                    "file_size": document.file_size,
                    "page_count": document.page_count,
                    "upload_date": document.upload_date.isoformat(),
                    "status": upload_status,
                    "error": error_message
                })

            except Exception as e:
                processing_errors.append(f"Failed to process {file.filename}: {str(e)}")
                # Clean up file if processing failed
                if os.path.exists(file_path):
                    os.remove(file_path)

        except Exception as e:
            processing_errors.append(f"Failed to upload {file.filename}: {str(e)}")

    return {
        "message": f"Processed {len(files)} files",
        "uploaded_documents": uploaded_documents,
        "errors": processing_errors,
        "summary": {
            "total_files": len(files),
            "successful_uploads": len(uploaded_documents),
            "failed_uploads": len(processing_errors)
        }
    }

@router.post("/query")
async def query_documents(query: str = Form(...), k: int = Form(3), db: Session = Depends(get_db)):
    """Basic document query endpoint"""
    try:
        # Get answer using RAG
        result = get_answer(query, k)
        
        # Log query to database
        query_record = Query(
            query_text=query,
            query_date=datetime.utcnow(),
            response=result.get("answer", ""),
            processing_time=result.get("processing_time", 0.0)
        )
        
        db.add(query_record)
        db.commit()

        return {
            "query": query,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "processing_time": result.get("processing_time", 0.0),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.get("/documents")
async def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents"""
    try:
        documents = db.query(Document).all()
        
        return {
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_size": doc.file_size,
                    "page_count": doc.page_count,
                    "upload_date": doc.upload_date.isoformat() if doc.upload_date else None
                }
                for doc in documents
            ],
            "total_count": len(documents)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")

@router.get("/document/{document_id}")
async def get_document_details(document_id: int, db: Session = Depends(get_db)):
    """Get details of a specific document"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "id": document.id,
            "filename": document.filename,
            "file_size": document.file_size,
            "page_count": document.page_count,
            "upload_date": document.upload_date.isoformat() if document.upload_date else None,
            "file_path": document.file_path
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document details: {str(e)}")

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Basic health check endpoint"""
    try:
        # Check database connection
        document_count = db.query(Document).count()
        
        # Check uploads directory
        uploads_exist = os.path.exists(UPLOAD_DIR)
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "connected": True,
                "document_count": document_count
            },
            "storage": {
                "uploads_directory": uploads_exist
            },
            "version": settings.app_version
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """Basic system statistics"""
    try:
        # Document statistics
        document_count = db.query(Document).count()
        
        # Query statistics (if Query table exists)
        try:
            from app.database import Query
            query_count = db.query(Query).count()
        except:
            query_count = 0

        # Storage statistics
        total_size = 0
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                filepath = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)

        return {
            "documents": {
                "total_count": document_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            },
            "queries": {
                "total_count": query_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")
