import PyPDF2
import os
import json
from datetime import datetime
from typing import Dict, Any, Tuple, List
from app.security import MAX_PAGES_PER_DOCUMENT

class DocumentProcessor:
    @staticmethod
    def extract_pdf_metadata(file_path: str) -> Dict[str, Any]:
        """Extract comprehensive metadata from PDF"""
        metadata = {
            "file_size": os.path.getsize(file_path),
            "processed_date": datetime.utcnow().isoformat(),
            "file_type": "PDF"
        }
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Basic PDF info
                metadata["page_count"] = len(pdf_reader.pages)
                metadata["is_encrypted"] = pdf_reader.is_encrypted
                
                # PDF metadata if available
                if pdf_reader.metadata:
                    pdf_metadata = pdf_reader.metadata
                    metadata.update({
                        "title": str(pdf_metadata.get('/Title', '')),
                        "author": str(pdf_metadata.get('/Author', '')),
                        "subject": str(pdf_metadata.get('/Subject', '')),
                        "creator": str(pdf_metadata.get('/Creator', '')),
                        "producer": str(pdf_metadata.get('/Producer', '')),
                        "creation_date": str(pdf_metadata.get('/CreationDate', '')),
                        "modification_date": str(pdf_metadata.get('/ModDate', ''))
                    })
                
                # Validate page count
                if metadata["page_count"] > MAX_PAGES_PER_DOCUMENT:
                    raise ValueError(f"Document has {metadata['page_count']} pages, maximum allowed is {MAX_PAGES_PER_DOCUMENT}")
                
        except Exception as e:
            metadata["extraction_error"] = str(e)
            
        return metadata
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text and metadata from PDF with enhanced error handling"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check page limit before processing
                if len(pdf_reader.pages) > MAX_PAGES_PER_DOCUMENT:
                    raise ValueError(f"Document exceeds maximum page limit of {MAX_PAGES_PER_DOCUMENT} pages")
                
                text = ""
                page_texts = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        text += page_text + "\n"
                        page_texts.append({
                            "page": page_num + 1,
                            "text_length": len(page_text),
                            "has_text": len(page_text.strip()) > 0
                        })
                    except Exception as e:
                        page_texts.append({
                            "page": page_num + 1,
                            "error": str(e),
                            "text_length": 0,
                            "has_text": False
                        })
                
                # Extract metadata
                metadata = DocumentProcessor.extract_pdf_metadata(file_path)
                metadata["page_details"] = page_texts
                metadata["total_text_length"] = len(text)
                metadata["extractable_pages"] = sum(1 for p in page_texts if p.get("has_text", False))
                
                return text.strip(), metadata
                
        except Exception as e:
            raise Exception(f"Error processing PDF {file_path}: {str(e)}")
    
    @staticmethod
    def validate_document_content(text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted document content"""
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check if document has extractable text
        if len(text.strip()) < 100:
            validation_result["warnings"].append("Document contains very little extractable text")
        
        # Check if document might be scanned (low text extraction rate)
        if metadata.get("extractable_pages", 0) < metadata.get("page_count", 1) * 0.5:
            validation_result["warnings"].append("Document may contain scanned pages with low text extraction rate")
        
        # Check for encrypted documents
        if metadata.get("is_encrypted", False):
            validation_result["warnings"].append("Document is encrypted")
        
        return validation_result

def process_file(file):
    """Legacy function for backward compatibility"""
    from PyPDF2 import PdfReader
    reader = PdfReader(file.file)
    text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
    
    # Use new chunking strategy
    from app.utils import chunk_text
    chunks = chunk_text(text)
    
    from app.embedding import store_chunks
    store_chunks(chunks)
