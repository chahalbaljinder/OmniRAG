import hashlib
from typing import List
from fastapi import HTTPException, UploadFile
import os

# File validation settings
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_FILES = 20
MAX_PAGES_PER_DOCUMENT = 1000
ALLOWED_MIME_TYPES = [
    'application/pdf',
    'application/x-pdf',
    'application/acrobat',
    'applications/vnd.pdf',
    'text/pdf',
    'text/x-pdf'
]

class SecurityValidator:
    @staticmethod
    def validate_file_type(file: UploadFile) -> bool:
        """Validate file type using both extension and magic bytes"""
        # Check file extension
        if not file.filename.lower().endswith('.pdf'):
            return False
        
        # Read first few bytes to check magic number
        file.file.seek(0)
        header = file.file.read(1024)
        file.file.seek(0)
        
        # PDF magic number check
        if not header.startswith(b'%PDF-'):
            return False
        
        return True
    
    @staticmethod
    def validate_file_size(file: UploadFile) -> bool:
        """Validate file size"""
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        return size <= MAX_FILE_SIZE
    
    @staticmethod
    def validate_files_count(files: List[UploadFile]) -> bool:
        """Validate number of files"""
        return len(files) <= MAX_FILES
    
    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        """Calculate SHA256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        # Remove path components and dangerous characters
        filename = os.path.basename(filename)
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        filename = filename.strip(". ")
        
        if not filename:
            filename = "unnamed_file.pdf"
        
        return filename
    
    @staticmethod
    def validate_query(query: str) -> bool:
        """Validate query input"""
        if not query or len(query.strip()) == 0:
            return False
        
        if len(query) > 5000:  # Max query length
            return False
        
        # Check for potential injection patterns
        dangerous_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
        query_lower = query.lower()
        
        for pattern in dangerous_patterns:
            if pattern in query_lower:
                return False
        
        return True

def validate_upload_files(files: List[UploadFile]) -> List[str]:
    """Comprehensive file validation"""
    errors = []
    
    if not SecurityValidator.validate_files_count(files):
        errors.append(f"Too many files. Maximum {MAX_FILES} files allowed.")
    
    for i, file in enumerate(files):
        if not SecurityValidator.validate_file_type(file):
            errors.append(f"File {i+1} ({file.filename}): Invalid file type. Only PDF files are allowed.")
        
        if not SecurityValidator.validate_file_size(file):
            errors.append(f"File {i+1} ({file.filename}): File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB.")
    
    return errors
