# app/rag.py (Updated for Gemini 2.0 Flash + Multi-document support + Source Metadata)

import os
import faiss
import pickle
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from app.utils import chunk_text
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_DIR = os.path.join(PROJECT_ROOT, "indexes")
FAISS_INDEX_DIR = os.path.join(PROJECT_ROOT, "faiss_index")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Debug: Print API key status
print(f"DEBUG: GEMINI_API_KEY loaded: {'Yes' if GEMINI_API_KEY else 'No'}")
if GEMINI_API_KEY:
    print(f"DEBUG: API key starts with: {GEMINI_API_KEY[:10]}...")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def ensure_json_serializable(obj):
    """Convert numpy types and other non-serializable types to native Python types"""
    import numpy as np
    
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: ensure_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [ensure_json_serializable(item) for item in obj]
    else:
        return obj


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
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        print("DEBUG: Model created successfully")
        response = model.generate_content(prompt)
        print("DEBUG: Content generated successfully")
        return response.text
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        return f"Gemini API error: {str(e)}"


def get_answer_with_sources(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Get answer for a query using enhanced RAG pipeline with source metadata
    
    Returns:
        Dict containing answer and source metadata for cross-checking
    """
    try:
        # Create query embedding
        query_embedding = embedding_model.encode([query])
        
        # Load FAISS index
        index_path = os.path.join(FAISS_INDEX_DIR, "index.faiss")
        metadata_path = os.path.join(FAISS_INDEX_DIR, "index.pkl")
        
        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            return {
                "answer": "No indexed documents found. Please upload and process documents first.",
                "sources": [],
                "query": query,
                "total_sources": 0,
                "timestamp": datetime.now().isoformat(),
                "error": "Index files not found"
            }
        
        index = faiss.read_index(index_path)
        
        # Load metadata
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
        
        # Search for similar chunks
        D, I = index.search(query_embedding, top_k)
        
        # Get relevant chunks with enhanced metadata
        relevant_chunks = []
        source_references = []
        
        for idx, score in zip(I[0], D[0]):
            if idx < len(metadata):
                chunk_data = metadata[idx]
                relevant_chunks.append(chunk_data)
                
                # Extract source information for references
                source_info = {
                    "document_name": chunk_data.get('source_file', 'Unknown Document'),
                    "document_id": str(chunk_data.get('document_id', 'Unknown ID')),
                    "page_number": chunk_data.get('page_number', 'N/A'),
                    "chunk_index": int(chunk_data.get('chunk_index', int(idx))),
                    "similarity_score": float(score),
                    "content_preview": chunk_data.get('content', '')[:100] + "..." if len(chunk_data.get('content', '')) > 100 else chunk_data.get('content', '')
                }
                
                # Add comprehensive case-specific information if available
                case_fields = [
                    'Case_Name', 'Case_No', 'Judges', 'Order_Date', 
                    'Adjudication_Deadline', 'Appellant', 'Appellant_Advocate',
                    'Respondents', 'Respondent_Advocates'
                ]
                
                for field in case_fields:
                    if field in chunk_data:
                        source_info[field] = chunk_data[field]
                
                # Also check legacy field names for backward compatibility
                legacy_mappings = {
                    'case_name': 'Case_Name',
                    'case_number': 'Case_No',
                    'court': 'Court',
                    'filing_date': 'Filing_Date'
                }
                
                for legacy_field, new_field in legacy_mappings.items():
                    if legacy_field in chunk_data and new_field not in source_info:
                        source_info[new_field] = chunk_data[legacy_field]
                
                source_references.append(source_info)
        
        # Create context from chunks
        context = "\n\n".join([chunk.get('content', '') for chunk in relevant_chunks])
        
        # Generate answer using LLM with source awareness
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {
                "answer": "Gemini API key not configured. Please add GEMINI_API_KEY to your .env file.",
                "sources": source_references,
                "query": query,
                "total_sources": len(source_references),
                "timestamp": datetime.now().isoformat(),
                "error": "API key missing"
            }
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        prompt = f"""
        Based on the following context from multiple documents, answer the query: {query}
        
        Context:
        {context}
        
        Please provide a comprehensive answer based on the given context. 
        When referencing specific information, try to indicate which source document it comes from.
        """
        
        response = model.generate_content(prompt)
        
        # Return structured response with sources - ensure all values are JSON serializable
        result = {
            "answer": response.text,
            "sources": source_references,
            "query": query,
            "total_sources": len(source_references),
            "timestamp": datetime.now().isoformat()
        }
        
        return ensure_json_serializable(result)
        
    except Exception as e:
        logger.error(f"Error in get_answer_with_sources: {str(e)}")
        result = {
            "answer": f"Error generating answer: {str(e)}",
            "sources": [],
            "query": query,
            "total_sources": 0,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
        return ensure_json_serializable(result)
