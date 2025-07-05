# app/api.py

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import os
import shutil
from datetime import datetime

from app.embedding import create_faiss_index
from app.rag import get_answer

router = APIRouter()
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory metadata store (can be moved to a real DB)
documents_metadata = {}

@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    if len(files) > 20:
        return JSONResponse(status_code=400, content={"error": "You can only upload up to 20 documents."})

    uploaded = []
    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Index the file
        try:
            chunk_count = create_faiss_index(file_path)
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": f"Failed to index {file.filename}: {str(e)}"})

        documents_metadata[file.filename] = {
            "filename": file.filename,
            "path": file_path,
            "chunks": chunk_count,
            "uploaded_at": datetime.now().isoformat()
        }
        uploaded.append({"filename": file.filename, "chunks": chunk_count})

    return {"status": "success", "uploaded": uploaded}


@router.post("/query")
async def query_documents(query: str = Form(...)):
    if not documents_metadata:
        return JSONResponse(status_code=400, content={"error": "No documents uploaded yet."})

    all_doc_paths = [doc["path"] for doc in documents_metadata.values()]
    try:
        answer = get_answer(query, all_doc_paths)
        return {"query": query, "answer": answer}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/documents")
async def list_documents():
    return {"documents": list(documents_metadata.values())}
