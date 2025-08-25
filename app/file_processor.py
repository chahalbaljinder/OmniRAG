import PyPDF2
import os
import json
from datetime import datetime
from typing import Dict, Any, Tuple, List

# Configuration constants
MAX_PAGES_PER_DOCUMENT = 1000

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
        """Extract text and metadata from PDF with enhanced error handling and page tracking"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check page limit before processing
                if len(pdf_reader.pages) > MAX_PAGES_PER_DOCUMENT:
                    raise ValueError(f"Document exceeds maximum page limit of {MAX_PAGES_PER_DOCUMENT} pages")
                
                text = ""
                page_texts = []
                page_contents = []  # Store page-wise content
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        text += page_text + "\n"
                        
                        # Store detailed page information
                        page_info = {
                            "page": page_num + 1,
                            "text_length": len(page_text),
                            "has_text": len(page_text.strip()) > 0,
                            "text_content": page_text.strip()  # Store actual text content
                        }
                        
                        # Extract law document specific patterns
                        law_patterns = DocumentProcessor._extract_law_patterns(page_text)
                        if law_patterns:
                            page_info["law_metadata"] = law_patterns
                        
                        page_texts.append(page_info)
                        page_contents.append({
                            "page_number": page_num + 1,
                            "content": page_text.strip(),
                            "law_metadata": law_patterns
                        })
                        
                    except Exception as e:
                        page_info = {
                            "page": page_num + 1,
                            "error": str(e),
                            "text_length": 0,
                            "has_text": False,
                            "text_content": ""
                        }
                        page_texts.append(page_info)
                
                # Extract metadata
                metadata = DocumentProcessor.extract_pdf_metadata(file_path)
                metadata["page_details"] = page_texts
                metadata["page_contents"] = page_contents  # Full page content for chunking
                metadata["total_text_length"] = len(text)
                metadata["extractable_pages"] = sum(1 for p in page_texts if p.get("has_text", False))
                
                # Add document-level law metadata
                metadata["document_type"] = DocumentProcessor._classify_document_type(text)
                metadata["law_summary"] = DocumentProcessor._extract_document_law_summary(text)
                
                return text.strip(), metadata
                
        except Exception as e:
            raise Exception(f"Error processing PDF {file_path}: {str(e)}")
    
    @staticmethod
    def _extract_law_patterns(text: str) -> Dict[str, Any]:
        """Extract law-specific patterns from text"""
        import re
        
        patterns = {}
        
        # Case numbers (various formats)
        case_patterns = [
            r'Case\s+No\.?\s*:?\s*([A-Z0-9\/\-\s]+)',
            r'Civil\s+Appeal\s+No\.?\s*:?\s*([0-9\/\-\s]+)',
            r'Criminal\s+Appeal\s+No\.?\s*:?\s*([0-9\/\-\s]+)',
            r'Writ\s+Petition\s+No\.?\s*:?\s*([0-9\/\-\s]+)',
            r'PIL\s+No\.?\s*:?\s*([0-9\/\-\s]+)'
        ]
        
        for pattern in case_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if 'case_numbers' not in patterns:
                    patterns['case_numbers'] = []
                patterns['case_numbers'].append(match.group(1).strip())
        
        # Court names
        court_patterns = [
            r'(Supreme\s+Court\s+of\s+India)',
            r'(High\s+Court\s+of\s+[A-Za-z\s]+)',
            r'([A-Za-z\s]+\s+High\s+Court)',
            r'(District\s+Court\s+[A-Za-z\s]+)',
            r'(Sessions\s+Court\s+[A-Za-z\s]+)'
        ]
        
        for pattern in court_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if 'courts' not in patterns:
                    patterns['courts'] = []
                patterns['courts'].append(match.group(1).strip())
        
        # Dates
        date_patterns = [
            r'(\d{1,2}[\-\/\.]\d{1,2}[\-\/\.]\d{4})',
            r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
            r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if 'dates' not in patterns:
                    patterns['dates'] = []
                patterns['dates'].append(match.group(1).strip())
        
        # Judge names (patterns like "Hon'ble Mr. Justice", "J.", etc.)
        judge_patterns = [
            r"Hon'ble\s+(?:Mr\.|Ms\.|Mrs\.)?\s*Justice\s+([A-Za-z\s\.]+?)(?:\s|,|\.)",
            r"Justice\s+([A-Za-z\s\.]+?)\s+J\.",
            r"([A-Za-z\s\.]+?)\s+J\."
        ]
        
        for pattern in judge_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if 'judges' not in patterns:
                    patterns['judges'] = []
                patterns['judges'].append(match.group(1).strip())
        
        # Legal sections/acts
        section_patterns = [
            r'Section\s+(\d+[A-Za-z]*(?:\(\d+\))?)\s+of\s+([A-Za-z\s,]+(?:Act|Code))',
            r'Article\s+(\d+[A-Za-z]*)\s+of\s+([A-Za-z\s]+)',
            r'Rule\s+(\d+[A-Za-z]*)\s+of\s+([A-Za-z\s,]+Rules?)'
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if 'legal_sections' not in patterns:
                    patterns['legal_sections'] = []
                patterns['legal_sections'].append({
                    'section': match.group(1).strip(),
                    'act': match.group(2).strip()
                })
        
        return patterns
    
    @staticmethod
    def _classify_document_type(text: str) -> str:
        """Classify the type of legal document"""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ['judgment', 'judgement', 'order', 'decided on']):
            return 'judgment'
        elif any(term in text_lower for term in ['petition', 'application', 'prayer']):
            return 'petition'
        elif any(term in text_lower for term in ['contract', 'agreement', 'deed']):
            return 'contract'
        elif any(term in text_lower for term in ['constitution', 'article']):
            return 'constitutional'
        elif any(term in text_lower for term in ['act', 'section', 'clause']):
            return 'statute'
        else:
            return 'general_legal'
    
    @staticmethod
    def _extract_document_law_summary(text: str) -> Dict[str, Any]:
        """Extract high-level summary information from legal document"""
        summary = {}
        
        # Extract case title (usually appears early in judgment)
        import re
        title_patterns = [
            r'([A-Z][A-Za-z\s&]+)\s+[Vv][Ss]?\.?\s+([A-Z][A-Za-z\s&]+)',
            r'In\s+the\s+matter\s+of:?\s*([A-Za-z\s&,]+)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text[:1000])  # Search in first 1000 chars
            if match:
                if 'vs' in pattern:
                    summary['parties'] = {
                        'petitioner': match.group(1).strip(),
                        'respondent': match.group(2).strip()
                    }
                else:
                    summary['subject_matter'] = match.group(1).strip()
                break
        
        return summary
    
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
