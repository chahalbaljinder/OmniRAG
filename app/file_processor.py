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
                
                # Extract case-specific metadata if available
                case_metadata = DocumentProcessor.extract_case_metadata(text)
                metadata.update(case_metadata)
                
                return text.strip(), metadata
                
        except Exception as e:
            raise Exception(f"Error processing PDF {file_path}: {str(e)}")
    
    @staticmethod
    def extract_case_metadata(text: str) -> Dict[str, Any]:
        """Extract comprehensive case-specific metadata from document text"""
        import re
        
        case_metadata = {}
        
        # Look for case names (common patterns)
        case_name_patterns = [
            r'(?:Case|Matter|Suit)?\s*(?:No\.?|Number)?\s*:?\s*([A-Z][a-zA-Z\s&]+v\.?\s+[A-Z][a-zA-Z\s&]+)',
            r'([A-Z][a-zA-Z\s&]+\s+v\.?\s+[A-Z][a-zA-Z\s&]+)',
            r'In\s+(?:the\s+)?(?:matter\s+)?of\s+([A-Z][a-zA-Z\s&,]+)',
            r'RE:\s*([A-Z][a-zA-Z\s&,]+)',
            r'BETWEEN\s*:\s*([A-Z][a-zA-Z\s&,]+)',
            r'PETITIONER\s*:\s*([A-Z][a-zA-Z\s&,]+)',
        ]
        
        for pattern in case_name_patterns:
            match = re.search(pattern, text[:3000], re.IGNORECASE)
            if match:
                case_metadata['Case_Name'] = match.group(1).strip()
                break
        
        # Look for case numbers with more comprehensive patterns
        case_number_patterns = [
            r'(?:Case|Suit|Matter|Docket|File)\s*(?:No\.?|Number)\s*:?\s*([\w\d\-/\(\)]+)',
            r'Civil\s*(?:Action|Case)\s*(?:No\.?)?\s*:?\s*([\w\d\-/\(\)]+)',
            r'Criminal\s*(?:Case)?\s*(?:No\.?)?\s*:?\s*([\w\d\-/\(\)]+)',
            r'(\d{4}-\d+-\d+)',  # Format like 2023-CV-1234
            r'(\d{2}-\d{4,6})',   # Format like 21-123456
            r'W\.P\.\(C\)\s*(?:No\.?)?\s*([\d/]+)',  # Writ Petition format
            r'C\.A\.\s*(?:No\.?)?\s*([\d/]+)',  # Civil Appeal format
            r'SLP\(C\)\s*(?:No\.?)?\s*([\d/]+)',  # Special Leave Petition format
        ]
        
        for pattern in case_number_patterns:
            match = re.search(pattern, text[:3000], re.IGNORECASE)
            if match:
                case_metadata['Case_No'] = match.group(1).strip()
                break
        
        # Look for judges
        judge_patterns = [
            r'(?:BEFORE|CORAM)\s*:?\s*(?:HON\'BLE\s+)?(?:JUSTICE\s+|J\.\s+)?([A-Z][A-Za-z\s,\.&]+?)(?:\n|\r|AND|$)',
            r'(?:HON\'BLE\s+)?(?:JUSTICE|J\.)\s+([A-Z][A-Za-z\s,\.&]+?)(?:\n|\r|AND|,)',
            r'PRESIDED\s+(?:OVER\s+)?BY\s*:?\s*([A-Z][A-Za-z\s,\.&]+?)(?:\n|\r)',
            r'(?:BENCH|COURT)\s*:?\s*([A-Z][A-Za-z\s,\.&]+?)(?:\n|\r)',
        ]
        
        judges = []
        for pattern in judge_patterns:
            matches = re.findall(pattern, text[:2000], re.IGNORECASE | re.MULTILINE)
            for match in matches:
                judge_name = match.strip().replace('HON\'BLE', '').replace('JUSTICE', '').replace('J.', '').strip()
                if len(judge_name) > 3 and judge_name not in judges:
                    judges.append(judge_name)
        
        if judges:
            case_metadata['Judges'] = judges
        
        # Look for order date
        order_date_patterns = [
            r'(?:ORDER|JUDGMENT|DECIDED)\s+(?:ON|DATE)\s*:?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
            r'(?:DATE|DECIDED)\s*:?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
            r'DATED\s*:?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
            r'([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{4})',  # General date format
        ]
        
        for pattern in order_date_patterns:
            match = re.search(pattern, text[:1500], re.IGNORECASE)
            if match:
                case_metadata['Order_Date'] = match.group(1).strip()
                break
        
        # Look for adjudication deadline
        deadline_patterns = [
            r'(?:HEARING|NEXT\s+DATE|ADJOURNED)\s+(?:TO|ON)\s*:?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
            r'(?:DEADLINE|DUE\s+DATE|LAST\s+DATE)\s*:?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
            r'(?:WITHIN|BY)\s+([0-9]{1,2}\s+(?:DAYS|WEEKS|MONTHS))',
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, text[:2000], re.IGNORECASE)
            if match:
                case_metadata['Adjudication_Deadline'] = match.group(1).strip()
                break
        
        # Look for appellant
        appellant_patterns = [
            r'APPELLANT\s*:?\s*([A-Z][A-Za-z\s,\.&\(\)]+?)(?:\n|\r|(?:VERSUS|V\.?|VS\.?))',
            r'PETITIONER\s*:?\s*([A-Z][A-Za-z\s,\.&\(\)]+?)(?:\n|\r|(?:VERSUS|V\.?|VS\.?))',
            r'APPLICANT\s*:?\s*([A-Z][A-Za-z\s,\.&\(\)]+?)(?:\n|\r|(?:VERSUS|V\.?|VS\.?))',
        ]
        
        for pattern in appellant_patterns:
            match = re.search(pattern, text[:2000], re.IGNORECASE)
            if match:
                case_metadata['Appellant'] = match.group(1).strip()
                break
        
        # Look for appellant advocate
        appellant_advocate_patterns = [
            r'(?:FOR\s+)?(?:APPELLANT|PETITIONER)\s*:?\s*(?:ADVOCATE\s+)?([A-Z][A-Za-z\s,\.&]+?)(?:\n|\r|FOR\s+RESPONDENT)',
            r'ADVOCATE\s+FOR\s+(?:APPELLANT|PETITIONER)\s*:?\s*([A-Z][A-Za-z\s,\.&]+?)(?:\n|\r)',
            r'(?:ADV\.|ADVOCATE)\s*:?\s*([A-Z][A-Za-z\s,\.&]+?)(?:\n|\r)',
        ]
        
        for pattern in appellant_advocate_patterns:
            match = re.search(pattern, text[:2000], re.IGNORECASE)
            if match:
                case_metadata['Appellant_Advocate'] = match.group(1).strip()
                break
        
        # Look for respondents
        respondent_patterns = [
            r'RESPONDENT\s*:?\s*([A-Z][A-Za-z\s,\.&\(\)]+?)(?:\n|\r|$)',
            r'(?:VERSUS|V\.?|VS\.?)\s+([A-Z][A-Za-z\s,\.&\(\)]+?)(?:\n|\r|$)',
            r'DEFENDANT\s*:?\s*([A-Z][A-Za-z\s,\.&\(\)]+?)(?:\n|\r|$)',
        ]
        
        respondents = []
        for pattern in respondent_patterns:
            matches = re.findall(pattern, text[:2000], re.IGNORECASE | re.MULTILINE)
            for match in matches:
                respondent_name = match.strip()
                if len(respondent_name) > 3 and respondent_name not in respondents:
                    respondents.append(respondent_name)
        
        if respondents:
            case_metadata['Respondents'] = respondents
        
        # Look for respondent advocates
        respondent_advocate_patterns = [
            r'(?:FOR\s+)?RESPONDENT\s*:?\s*(?:ADVOCATE\s+)?([A-Z][A-Za-z\s,\.&]+?)(?:\n|\r|$)',
            r'ADVOCATE\s+FOR\s+RESPONDENT\s*:?\s*([A-Z][A-Za-z\s,\.&]+?)(?:\n|\r|$)',
        ]
        
        respondent_advocates = []
        for pattern in respondent_advocate_patterns:
            matches = re.findall(pattern, text[:2000], re.IGNORECASE | re.MULTILINE)
            for match in matches:
                advocate_name = match.strip()
                if len(advocate_name) > 3 and advocate_name not in respondent_advocates:
                    respondent_advocates.append(advocate_name)
        
        if respondent_advocates:
            case_metadata['Respondent_Advocates'] = respondent_advocates
        
        return case_metadata
    
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
