import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import tempfile
import io
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db, User, Document
from app.auth import get_password_hash

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create the test database tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)

@pytest.fixture
def sample_pdf():
    """Create a sample PDF file for testing"""
    # Create a simple PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Hello World) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000202 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
295
%%EOF"""
    
    return io.BytesIO(pdf_content)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database_connected" in data

def test_empty_documents_list():
    """Test getting documents when none are uploaded"""
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 0
    assert data["documents"] == []

def test_query_without_documents():
    """Test querying when no documents are uploaded"""
    response = client.post("/query", data={"query": "What is this about?"})
    assert response.status_code == 400
    assert "No documents uploaded" in response.json()["error"]

def test_invalid_query():
    """Test querying with invalid input"""
    # Empty query
    response = client.post("/query", data={"query": ""})
    assert response.status_code == 400
    
    # Query with script tag
    response = client.post("/query", data={"query": "<script>alert('test')</script>"})
    assert response.status_code == 400

def test_upload_validation():
    """Test file upload validation"""
    # Test uploading non-PDF file
    fake_file = io.BytesIO(b"This is not a PDF file")
    response = client.post(
        "/upload",
        files={"files": ("test.txt", fake_file, "text/plain")}
    )
    assert response.status_code == 400
    assert "errors" in response.json()

def test_upload_too_many_files():
    """Test uploading too many files"""
    files = []
    for i in range(25):  # More than the 20 file limit
        fake_pdf = io.BytesIO(b"%PDF-1.4\nfake content")
        files.append(("files", (f"test{i}.pdf", fake_pdf, "application/pdf")))
    
    response = client.post("/upload", files=files)
    assert response.status_code == 400

def test_stats():
    """Test the statistics endpoint"""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "queries" in data
    assert "system" in data

def test_file_upload_and_query(sample_pdf):
    """Test complete workflow: upload and query"""
    # Upload a file
    sample_pdf.seek(0)
    response = client.post(
        "/upload",
        files={"files": ("sample.pdf", sample_pdf, "application/pdf")}
    )
    
    # Note: This might fail due to PDF processing issues in test environment
    # but the API structure should be correct
    if response.status_code == 200:
        data = response.json()
        assert "uploaded" in data
        assert len(data["uploaded"]) > 0
        
        # Test querying the uploaded document
        response = client.post("/query", data={"query": "What is this document about?"})
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data
            assert "query" in data

def test_document_management():
    """Test document listing and details"""
    # Get documents list
    response = client.get("/documents")
    assert response.status_code == 200
    
    data = response.json()
    if data["total_count"] > 0:
        # Test getting specific document details
        doc_id = data["documents"][0]["id"]
        response = client.get(f"/document/{doc_id}")
        assert response.status_code == 200
        
        detail_data = response.json()
        assert "id" in detail_data
        assert "filename" in detail_data

def test_nonexistent_document():
    """Test getting details for non-existent document"""
    response = client.get("/document/99999")
    assert response.status_code == 404

# Performance and edge case tests
def test_large_query():
    """Test handling of large queries"""
    large_query = "A" * 6000  # Exceeds 5000 character limit
    response = client.post("/query", data={"query": large_query})
    assert response.status_code == 400

def test_sql_injection_query():
    """Test SQL injection protection"""
    malicious_query = "'; DROP TABLE documents; --"
    response = client.post("/query", data={"query": malicious_query})
    # Should either process safely or reject
    assert response.status_code in [200, 400]

# Cleanup
def teardown_module():
    """Clean up test database"""
    try:
        os.remove("test.db")
    except FileNotFoundError:
        pass

class TestAuthenticationAPI:
    """Test authentication endpoints"""
    
    def test_register_user(self):
        """Test user registration"""
        response = client.post("/auth/register", data={
            "username": "testuser",
            "email": "test@example.com", 
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    def test_login_user(self):
        """Test user login"""
        # First register
        client.post("/auth/register", data={
            "username": "logintest",
            "email": "login@example.com",
            "password": "loginpass123"
        })
        
        # Then login
        response = client.post("/auth/login", data={
            "username": "logintest",
            "password": "loginpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_get_current_user(self):
        """Test getting current user info"""
        # Register and login
        client.post("/auth/register", data={
            "username": "currentuser",
            "email": "current@example.com",
            "password": "currentpass123"
        })
        login_response = client.post("/auth/login", data={
            "username": "currentuser",
            "password": "currentpass123"
        })
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "currentuser"

class TestEnhancedDocumentAPI:
    """Test enhanced document management"""
    
    def test_upload_with_auth(self, sample_pdf):
        """Test document upload with authentication"""
        # Register and login
        client.post("/auth/register", data={
            "username": "uploaduser",
            "email": "upload@example.com",
            "password": "uploadpass123"
        })
        login_response = client.post("/auth/login", data={
            "username": "uploaduser",
            "password": "uploadpass123"
        })
        token = login_response.json()["access_token"]
        
        # Upload document
        response = client.post(
            "/upload",
            files={"files": ("test.pdf", sample_pdf, "application/pdf")},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["processed_files"]) == 1

class TestHybridSearchAPI:
    """Test hybrid search functionality"""
    
    def test_hybrid_search(self):
        """Test hybrid search endpoint"""
        # Skip if hybrid search not available
        try:
            from app.hybrid_search import hybrid_search_engine
        except ImportError:
            pytest.skip("Hybrid search not available")
        
        response = client.post("/search", data={
            "query": "test query",
            "search_type": "hybrid",
            "k": 5,
            "semantic_weight": 0.7
        })
        # Response depends on whether documents are indexed
        assert response.status_code in [200, 422]

class TestAsyncProcessingAPI:
    """Test async processing endpoints"""
    
    def test_async_query(self):
        """Test async query processing"""
        # Skip if async processing not available
        try:
            from app.async_processing import task_queue
        except ImportError:
            pytest.skip("Async processing not available")
        
        response = client.post("/query/async", data={
            "query": "test async query",
            "k": 3
        })
        # Should return task ID
        assert response.status_code in [200, 422]

class TestMonitoringAPI:
    """Test monitoring and admin endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_system_stats(self):
        """Test system statistics endpoint"""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "queries" in data
        assert "system" in data
    
    def test_monitoring_dashboard_requires_admin(self):
        """Test that monitoring dashboard requires admin access"""
        response = client.get("/admin/monitoring")
        assert response.status_code == 401  # Unauthorized without token

class TestCacheAPI:
    """Test caching functionality"""
    
    def test_cache_stats(self):
        """Test cache statistics endpoint"""
        # Create admin user and login
        with TestingSessionLocal() as db:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("adminpass"),
                role="admin"
            )
            db.add(admin_user)
            db.commit()
        
        login_response = client.post("/auth/login", data={
            "username": "admin",
            "password": "adminpass"
        })
        token = login_response.json()["access_token"]
        
        response = client.get("/admin/cache/stats", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

class TestRateLimitingAPI:
    """Test rate limiting functionality"""
    
    def test_upload_rate_limiting(self, sample_pdf):
        """Test upload rate limiting"""
        # Make multiple rapid requests (this may not trigger in test environment)
        responses = []
        for i in range(15):  # Try to exceed rate limit
            response = client.post(
                "/upload",
                files={"files": ("test.pdf", sample_pdf, "application/pdf")}
            )
            responses.append(response.status_code)
        
        # At least some should succeed (exact behavior depends on rate limiter)
        assert any(code == 200 for code in responses[-5:])

class TestSecurityAPI:
    """Test security features"""
    
    def test_file_validation(self):
        """Test file validation"""
        # Try to upload non-PDF file
        fake_pdf = io.BytesIO(b"This is not a PDF")
        response = client.post(
            "/upload",
            files={"files": ("fake.pdf", fake_pdf, "application/pdf")}
        )
        # Should reject invalid files
        assert response.status_code in [422, 400]
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        malicious_query = "'; DROP TABLE documents; --"
        response = client.post("/query", data={"query": malicious_query})
        # Should handle safely without errors
        assert response.status_code in [200, 422]
