# app/api_basic.py - Simplified Basic API with minimal features

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import shutil
import time
import json
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
                    file_hash=f"hash_{int(time.time())}",  # Simple hash
                    file_metadata=json.dumps(pdf_metadata)  # Store full metadata as JSON
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
            "page_references": result.get("page_references", []),
            "total_chunks_found": result.get("total_chunks_found", 0),
            "query_type": result.get("query_type", "basic"),
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

@router.delete("/documents/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a specific document and its associated index"""
    try:
        # Find the document
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document_filename = document.filename
        
        # Delete associated index files
        index_file = os.path.join(PROJECT_ROOT, "indexes", f"{document_filename}.index")
        meta_file = index_file + ".meta"
        
        deleted_files = []
        if os.path.exists(index_file):
            os.remove(index_file)
            deleted_files.append(f"{document_filename}.index")
        
        if os.path.exists(meta_file):
            os.remove(meta_file)
            deleted_files.append(f"{document_filename}.index.meta")
        
        # Delete the actual file
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
            deleted_files.append(document_filename)
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        return {
            "message": f"Document '{document_filename}' deleted successfully",
            "document_id": document_id,
            "deleted_files": deleted_files,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.delete("/knowledge-base")
async def clear_knowledge_base(db: Session = Depends(get_db)):
    """Clear all documents, embeddings, and knowledge base"""
    try:
        # Get all documents before deletion for response
        documents = db.query(Document).all()
        document_count = len(documents)
        
        # Delete all index files
        indexes_dir = os.path.join(PROJECT_ROOT, "indexes")
        deleted_indexes = []
        
        if os.path.exists(indexes_dir):
            for filename in os.listdir(indexes_dir):
                file_path = os.path.join(indexes_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_indexes.append(filename)
        
        # Delete all uploaded files
        uploads_dir = os.path.join(PROJECT_ROOT, "uploads")
        deleted_uploads = []
        
        if os.path.exists(uploads_dir):
            for filename in os.listdir(uploads_dir):
                file_path = os.path.join(uploads_dir, filename)
                if os.path.isfile(file_path) and filename.endswith('.pdf'):
                    os.remove(file_path)
                    deleted_uploads.append(filename)
        
        # Delete all documents from database
        db.query(Document).delete()
        
        # Also delete all query records
        try:
            db.query(Query).delete()
            query_records_deleted = True
        except:
            query_records_deleted = False
        
        db.commit()
        
        return {
            "message": "Knowledge base cleared successfully",
            "deleted_documents": document_count,
            "deleted_index_files": len(deleted_indexes),
            "deleted_upload_files": len(deleted_uploads),
            "query_records_cleared": query_records_deleted,
            "details": {
                "index_files": deleted_indexes,
                "upload_files": deleted_uploads
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear knowledge base: {str(e)}")

@router.get("/document/{document_id}/metadata")
async def get_document_metadata(document_id: int, db: Session = Depends(get_db)):
    """Get detailed metadata for a specific document including law-specific information"""
    try:
        # Find the document
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Parse stored metadata
        metadata = {}
        if document.file_metadata:
            try:
                import json
                metadata = json.loads(document.file_metadata)
            except:
                metadata = {}
        
        # Get fresh metadata from file if it still exists
        if os.path.exists(document.file_path):
            try:
                from app.file_processor import DocumentProcessor
                _, fresh_metadata = DocumentProcessor.extract_text_from_pdf(document.file_path)
                metadata.update(fresh_metadata)
            except Exception as e:
                metadata["metadata_extraction_error"] = str(e)
        
        response = {
            "document_id": document.id,
            "filename": document.filename,
            "file_size": document.file_size,
            "page_count": document.page_count,
            "upload_date": document.upload_date.isoformat() if document.upload_date else None,
            "metadata": metadata,
            "law_analysis": {
                "document_type": metadata.get("document_type", "unknown"),
                "law_summary": metadata.get("law_summary", {}),
                "has_law_metadata": bool(metadata.get("page_details", []) and 
                                       any(page.get("law_metadata") for page in metadata.get("page_details", [])))
            }
        }
        
        # Add page-wise law metadata summary
        if metadata.get("page_details"):
            law_elements = {
                "case_numbers": set(),
                "courts": set(),
                "judges": set(),
                "legal_sections": []
            }
            
            for page in metadata.get("page_details", []):
                page_law_data = page.get("law_metadata", {})
                if page_law_data:
                    for case_num in page_law_data.get("case_numbers", []):
                        law_elements["case_numbers"].add(case_num)
                    for court in page_law_data.get("courts", []):
                        law_elements["courts"].add(court)
                    for judge in page_law_data.get("judges", []):
                        law_elements["judges"].add(judge)
                    law_elements["legal_sections"].extend(page_law_data.get("legal_sections", []))
            
            response["law_analysis"]["extracted_elements"] = {
                "case_numbers": list(law_elements["case_numbers"]),
                "courts": list(law_elements["courts"]),
                "judges": list(law_elements["judges"]),
                "legal_sections": law_elements["legal_sections"]
            }
        
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document metadata: {str(e)}")
