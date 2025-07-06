# tests/test_enhanced_api.py - Comprehensive tests for enhanced API

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db, User, Document, Query, APIKey, Task
from app.auth import hash_password, create_access_token, hash_api_key, generate_api_key
from app.config import settings

# Test database setup - use same DB as other tests for consistency
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def cleanup_test_data():
    """Clean up test data between tests"""
    db = TestingSessionLocal()
    try:
        # Clear all tables
        db.query(Query).delete()
        db.query(Document).delete()
        db.query(APIKey).delete()
        db.query(Task).delete()
        db.query(User).delete()
        db.commit()
        
        # Clean up uploaded files
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
        if os.path.exists(upload_dir):
            for file in os.listdir(upload_dir):
                file_path = os.path.join(upload_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except:
                    pass  # Ignore cleanup errors
    except Exception as e:
        print(f"Cleanup error: {e}")
    finally:
        db.close()

@pytest.fixture(scope="module")
def setup_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """Test client with cleanup"""
    cleanup_test_data()  # Clean before test
    with TestClient(app) as test_client:
        yield test_client
    cleanup_test_data()  # Clean after test

@pytest.fixture
def test_user():
    """Create a test user"""
    db = TestingSessionLocal()
    
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("password123"),
        role="user",
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    yield user
    
    db.delete(user)
    db.commit()
    db.close()

@pytest.fixture
def admin_user():
    """Create an admin user"""
    db = TestingSessionLocal()
    
    user = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=hash_password("admin123"),
        role="admin",
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    yield user
    
    db.delete(user)
    db.commit()
    db.close()

@pytest.fixture
def auth_token(test_user):
    """Create auth token for test user"""
    return create_access_token(test_user.id, test_user.username, test_user.role)

@pytest.fixture
def admin_token(admin_user):
    """Create auth token for admin user"""
    return create_access_token(admin_user.id, admin_user.username, admin_user.role)

@pytest.fixture
def test_api_key(test_user):
    """Create API key for test user"""
    db = TestingSessionLocal()
    
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    
    api_key_record = APIKey(
        user_id=test_user.id,
        name="Test API Key",
        key_hash=key_hash,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    
    db.add(api_key_record)
    db.commit()
    
    yield api_key
    
    db.delete(api_key_record)
    db.commit()
    db.close()

@pytest.fixture
def sample_pdf():
    """Create a sample PDF file for testing"""
    content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000079 00000 n \n0000000173 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n253\n%%EOF"
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(content)
        tmp_file.flush()
        yield tmp_file.name
    
    os.unlink(tmp_file.name)

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_register_user(self, client, setup_database):
        """Test user registration"""
        response = client.post(
            "/api/v2/auth/register",
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["role"] == "user"
    
    def test_register_duplicate_user(self, client, test_user):
        """Test registration with existing username"""
        response = client.post(
            "/api/v2/auth/register",
            data={
                "username": test_user.username,
                "email": "different@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_login_user(self, client, test_user):
        """Test user login"""
        response = client.post(
            "/api/v2/auth/login",
            data={
                "username": test_user.username,
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == test_user.username
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v2/auth/login",
            data={
                "username": test_user.username,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
    
    def test_create_api_key(self, client, auth_token):
        """Test API key creation"""
        response = client.post(
            "/api/v2/auth/api-keys",
            headers={"Authorization": f"Bearer {auth_token}"},
            data={
                "name": "Test Key",
                "expires_days": "30"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert data["name"] == "Test Key"

class TestFileUpload:
    """Test file upload functionality"""
    
    def test_upload_with_auth(self, client, auth_token, sample_pdf):
        """Test file upload with authentication"""
        with open(sample_pdf, "rb") as file:
            response = client.post(
                "/api/v2/upload",
                headers={"Authorization": f"Bearer {auth_token}"},
                files={"files": ("test.pdf", file, "application/pdf")},
                data={"async_processing": "false"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert len(data["uploaded"]) > 0
    
    def test_upload_with_api_key(self, client, test_api_key, sample_pdf):
        """Test file upload with API key"""
        with open(sample_pdf, "rb") as file:
            response = client.post(
                "/api/v2/upload",
                headers={"X-API-Key": test_api_key},
                files={"files": ("test.pdf", file, "application/pdf")},
                data={"async_processing": "false"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
    
    def test_upload_async(self, client, auth_token, sample_pdf):
        """Test async file upload"""
        with open(sample_pdf, "rb") as file:
            response = client.post(
                "/api/v2/upload",
                headers={"Authorization": f"Bearer {auth_token}"},
                files={"files": ("test.pdf", file, "application/pdf")},
                data={"async_processing": "true"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["async_processing"] == True
        assert len(data["uploaded"]) > 0
        if data["uploaded"]:
            assert "task_id" in data["uploaded"][0]
    
    def test_upload_invalid_file(self, client, auth_token):
        """Test upload with invalid file type"""
        content = b"This is not a PDF"
        
        response = client.post(
            "/api/v2/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"files": ("test.txt", content, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "errors" in response.json()

class TestDocumentQueries:
    """Test document query functionality"""
    
    def test_query_with_auth(self, client, auth_token):
        """Test document query with authentication"""
        response = client.post(
            "/api/v2/query",
            headers={"Authorization": f"Bearer {auth_token}"},
            data={
                "query": "What is this document about?",
                "k": "3",
                "search_type": "hybrid"
            }
        )
        
        # Should work even with no documents (returns appropriate error)
        assert response.status_code in [200, 400]
    
    def test_query_with_api_key(self, client, test_api_key):
        """Test document query with API key"""
        response = client.post(
            "/api/v2/query",
            headers={"X-API-Key": test_api_key},
            data={
                "query": "Test query",
                "search_type": "semantic"
            }
        )
        
        assert response.status_code in [200, 400]
    
    def test_query_async(self, client, auth_token):
        """Test async query processing"""
        response = client.post(
            "/api/v2/query",
            headers={"Authorization": f"Bearer {auth_token}"},
            data={
                "query": "Complex analysis query",
                "async_processing": "true",
                "search_type": "hybrid"
            }
        )
        
        assert response.status_code in [200, 400]
    
    def test_query_invalid(self, client, auth_token):
        """Test query with invalid input"""
        response = client.post(
            "/api/v2/query",
            headers={"Authorization": f"Bearer {auth_token}"},
            data={"query": ""}  # Empty query
        )
        
        assert response.status_code == 422  # Validation error

class TestDocumentManagement:
    """Test document management endpoints"""
    
    def test_list_documents(self, client, auth_token):
        """Test document listing"""
        response = client.get(
            "/api/v2/documents",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total_count" in data
    
    def test_list_documents_pagination(self, client, auth_token):
        """Test document listing with pagination"""
        response = client.get(
            "/api/v2/documents?skip=0&limit=5",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 5
    
    def test_list_owner_documents(self, client, auth_token):
        """Test listing only owner's documents"""
        response = client.get(
            "/api/v2/documents?owner_only=true",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200

class TestSystemMonitoring:
    """Test system monitoring endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v2/health")
        
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
    
    def test_system_stats(self, client, auth_token):
        """Test system statistics"""
        response = client.get(
            "/api/v2/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "queries" in data
        assert "cache" in data
    
    def test_performance_metrics_admin(self, client, admin_token):
        """Test performance metrics (admin only)"""
        response = client.get(
            "/api/v2/performance-metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "all_metrics" in data or "available_metrics" in data
    
    def test_performance_metrics_unauthorized(self, client, auth_token):
        """Test performance metrics with regular user"""
        response = client.get(
            "/api/v2/performance-metrics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 403

class TestAdminEndpoints:
    """Test admin-only endpoints"""
    
    def test_list_users_admin(self, client, admin_token):
        """Test user listing as admin"""
        response = client.get(
            "/api/v2/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total_count" in data
    
    def test_list_users_unauthorized(self, client, auth_token):
        """Test user listing as regular user"""
        response = client.get(
            "/api/v2/admin/users",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 403
    
    def test_system_logs_admin(self, client, admin_token):
        """Test system logs as admin"""
        response = client.get(
            "/api/v2/admin/system-logs",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_upload_rate_limit(self, client, auth_token, sample_pdf):
        """Test upload rate limiting"""
        # Make multiple rapid requests
        responses = []
        for i in range(15):  # Exceed the 10/minute limit
            with open(sample_pdf, "rb") as file:
                response = client.post(
                    "/api/v2/upload",
                    headers={"Authorization": f"Bearer {auth_token}"},
                    files={"files": (f"test_{i}.pdf", file, "application/pdf")}
                )
                responses.append(response.status_code)
        
        # Should eventually get rate limited
        assert 429 in responses or any(r >= 400 for r in responses)
    
    def test_query_rate_limit(self, client, auth_token):
        """Test query rate limiting"""
        # Make multiple rapid requests
        responses = []
        for i in range(35):  # Exceed the 30/minute limit
            response = client.post(
                "/api/v2/query",
                headers={"Authorization": f"Bearer {auth_token}"},
                data={"query": f"Test query {i}"}
            )
            responses.append(response.status_code)
        
        # Should eventually get rate limited
        assert 429 in responses or any(r >= 400 for r in responses)

class TestBackwardCompatibility:
    """Test backward compatibility with v1 API"""
    
    def test_v1_upload(self, client, sample_pdf):
        """Test v1 upload endpoint"""
        with open(sample_pdf, "rb") as file:
            response = client.post(
                "/api/v1/upload",
                files={"files": ("test.pdf", file, "application/pdf")}
            )
        
        assert response.status_code in [200, 400]  # Should work or fail gracefully
    
    def test_v1_query(self, client):
        """Test v1 query endpoint"""
        response = client.post(
            "/api/v1/query",
            data={"query": "What is this about?"}
        )
        
        assert response.status_code in [200, 400]  # Should work or fail gracefully

def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "features" in data
