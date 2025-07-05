# app/rag.py (Updated for Gemini 2.0 Flash + Multi-document support)

import os
import faiss
import pickle
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from app.utils import chunk_text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_DIR = os.path.join(PROJECT_ROOT, "indexes")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Debug: Print API key status
print(f"DEBUG: GEMINI_API_KEY loaded: {'Yes' if GEMINI_API_KEY else 'No'}")
if GEMINI_API_KEY:
    print(f"DEBUG: API key starts with: {GEMINI_API_KEY[:10]}...")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def get_answer(query, doc_paths, k=2):
    if not isinstance(doc_paths, list):
        doc_paths = [doc_paths]

    all_chunks = []

    for doc_path in doc_paths:
        index_file = os.path.join(INDEX_DIR, os.path.basename(doc_path) + ".index")
        if not os.path.exists(index_file):
            continue

        index = faiss.read_index(index_file)
        with open(index_file + ".meta", "rb") as f:
            chunks = pickle.load(f)

        query_embedding = embedding_model.encode([query])
        _, indices = index.search(query_embedding, k)
        relevant_chunks = [chunks[i] for i in indices[0] if i < len(chunks)]
        all_chunks.extend(relevant_chunks)

    if not all_chunks:
        return "No relevant content found across uploaded documents."

    # Prepare context
    context = "\n---\n".join(all_chunks)
    prompt = f"""You are a helpful assistant. Use the context below to answer the question.

Context:
{context}

Question: {query}
Answer:"""

    # Call Gemini 2.0 Flash
    try:
        # Get API key fresh each time to ensure it's loaded
        api_key = os.getenv("GEMINI_API_KEY")
        print(f"DEBUG: Fresh API key check: {'Present' if api_key else 'Missing'}")
        
        if not api_key:
            return "Gemini API key not configured. Please add GEMINI_API_KEY to your .env file."
        
        # Configure Gemini with fresh API key
        genai.configure(api_key=api_key)
        print(f"DEBUG: About to call Gemini with API key: {api_key[:10]}...")
        
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("DEBUG: Model created successfully")
        response = model.generate_content(prompt)
        print("DEBUG: Content generated successfully")
        return response.text
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        return f"Gemini API error: {str(e)}"
