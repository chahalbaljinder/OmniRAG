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
    """Get answer for query using all available documents with enhanced metadata"""
    try:
        # Get all available index files
        if not os.path.exists(INDEX_DIR):
            return {
                "answer": "No documents have been indexed yet. Please upload some documents first.",
                "sources": [],
                "processing_time": 0.0,
                "page_references": []
            }
        
        all_chunks = []
        sources = []
        page_references = []
        
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
                    distances, indices = index.search(query_embedding, min(k, len(chunks)))
                    
                    # Add relevant chunks with metadata
                    document_name = filename.replace(".index", "")
                    for i, distance in zip(indices[0], distances[0]):
                        if i < len(chunks) and i >= 0:
                            chunk_data = chunks[i]
                            
                            # Handle both string chunks and dictionary chunks
                            if isinstance(chunk_data, dict):
                                chunk_content = chunk_data.get('content', str(chunk_data))
                                page_num = chunk_data.get('page_number', chunk_data.get('source_page', 'Unknown'))
                                law_metadata = chunk_data.get('law_metadata', {})
                            else:
                                chunk_content = str(chunk_data)
                                page_num = 'Unknown'
                                law_metadata = {}
                            
                            all_chunks.append(chunk_content)
                            sources.append(document_name)
                            
                            # Create page reference with law metadata
                            page_ref = {
                                'document': document_name,
                                'page': page_num,
                                'relevance_score': float(1.0 - distance),  # Convert distance to similarity
                                'law_metadata': law_metadata
                            }
                            page_references.append(page_ref)
                            
                except Exception as e:
                    print(f"Error processing index {filename}: {str(e)}")
                    continue
        
        if not all_chunks:
            return {
                "answer": "No relevant content found in uploaded documents.",
                "sources": [],
                "processing_time": 0.0,
                "page_references": []
            }

        # Sort by relevance and limit chunks
        sorted_refs = sorted(page_references, key=lambda x: x['relevance_score'], reverse=True)
        top_chunks = [all_chunks[i] for i, _ in enumerate(sorted_refs[:10])]
        top_page_refs = sorted_refs[:10]

        # Prepare context with page attribution
        context_parts = []
        for i, (chunk, ref) in enumerate(zip(top_chunks, top_page_refs)):
            page_info = f"[Page {ref['page']} of {ref['document']}]"
            context_parts.append(f"{page_info}\n{chunk}")
        
        context = "\n---\n".join(context_parts)
        
        # Enhanced prompt for law documents
        prompt = f"""You are a legal assistant AI. Use the context below to answer the question. 
        Include specific page references and case details when available.

Context from legal documents:
{context}

Question: {query}

Please provide a comprehensive answer with:
1. Direct answer to the question
2. Relevant page references 
3. Any case numbers, court names, or legal sections mentioned
4. Source document names

Answer:"""

        # Call Gemini 2.0 Flash
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {
                "answer": "Gemini API key not configured. Please add GEMINI_API_KEY to your .env file.",
                "sources": sources,
                "processing_time": 0.0,
                "page_references": top_page_refs
            }
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        
        return {
            "answer": response.text,
            "sources": list(set(sources[:5])),  # Unique sources, max 5
            "processing_time": 0.0,
            "page_references": top_page_refs,
            "total_chunks_found": len(all_chunks),
            "query_type": "legal_enhanced"
        }
        
    except Exception as e:
        return {
            "answer": f"Error processing query: {str(e)}",
            "sources": [],
            "processing_time": 0.0,
            "page_references": []
        }
