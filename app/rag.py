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


def get_answer(query, k=3):
    """Get answer for query using all available documents"""
    try:
        # Get all available index files
        if not os.path.exists(INDEX_DIR):
            return {
                "answer": "No documents have been indexed yet. Please upload some documents first.",
                "sources": [],
                "processing_time": 0.0
            }
        
        all_chunks = []
        sources = []
        
        # Search through all available indexes
        for filename in os.listdir(INDEX_DIR):
            if filename.endswith(".index"):
                index_file = os.path.join(INDEX_DIR, filename)
                meta_file = index_file + ".meta"
                
                if not os.path.exists(meta_file):
                    continue
                
                try:
                    # Load index and metadata
                    index = faiss.read_index(index_file)
                    with open(meta_file, "rb") as f:
                        chunks = pickle.load(f)
                    
                    # Search for relevant chunks
                    query_embedding = embedding_model.encode([query])
                    _, indices = index.search(query_embedding, min(k, len(chunks)))
                    
                    # Add relevant chunks
                    document_name = filename.replace(".index", "")
                    for i in indices[0]:
                        if i < len(chunks) and i >= 0:
                            all_chunks.append(chunks[i])
                            sources.append(document_name)
                            
                except Exception as e:
                    print(f"Error processing index {filename}: {str(e)}")
                    continue
        
        if not all_chunks:
            return {
                "answer": "No relevant content found in uploaded documents.",
                "sources": [],
                "processing_time": 0.0
            }

        # Prepare context (limit to avoid token limits)
        context = "\n---\n".join(all_chunks[:10])  # Limit to first 10 chunks
        prompt = f"""You are a helpful assistant. Use the context below to answer the question.

Context:
{context}

Question: {query}
Answer:"""

        # Call Gemini 2.0 Flash
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {
                "answer": "Gemini API key not configured. Please add GEMINI_API_KEY to your .env file.",
                "sources": sources,
                "processing_time": 0.0
            }
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        
        return {
            "answer": response.text,
            "sources": list(set(sources[:5])),  # Unique sources, max 5
            "processing_time": 0.0
        }
        
    except Exception as e:
        return {
            "answer": f"Error processing query: {str(e)}",
            "sources": [],
            "processing_time": 0.0
        }
