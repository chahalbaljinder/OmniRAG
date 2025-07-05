# app/embedding.py

import os
import faiss
import pickle
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
from app.utils import chunk_text

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Directory to store FAISS indexes
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_DIR = os.path.join(PROJECT_ROOT, "indexes")
os.makedirs(INDEX_DIR, exist_ok=True)

def create_faiss_index(file_path):
    # Extract text from PDF
    reader = PdfReader(file_path)
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)

    # Chunk text
    chunks = chunk_text(full_text, max_length=300)
    chunk_count = len(chunks)

    # Get embeddings
    embeddings = embedding_model.encode(chunks)

    # Create FAISS index
    dim = embeddings[0].shape[0]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Save index
    index_file = os.path.join(INDEX_DIR, os.path.basename(file_path) + ".index")
    faiss.write_index(index, index_file)

    # Save mapping of chunk -> text
    with open(index_file + ".meta", "wb") as f:
        pickle.dump(chunks, f)

    return chunk_count
