import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def upload_file():
    test_file_path = "tests/sample.pdf"
    with open(test_file_path, "rb") as f:
        response = client.post("/upload", files={"files": ("sample.pdf", f, "application/pdf")})
    assert response.status_code == 200
    return response.json()

def test_upload(upload_file):
    assert "uploaded" in upload_file
    assert upload_file["uploaded"][0]["filename"] == "sample.pdf"

def test_query(upload_file):
    response = client.post("/query", data={"query": "What is this document about?"})
    assert response.status_code == 200
    assert "answer" in response.json()
