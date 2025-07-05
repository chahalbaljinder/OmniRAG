# app/embedding.py - Enhanced embedding system with database integration

import os
import faiss
import pickle
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple
from app.utils import chunk_text, log_performance
import time
import logging

logger = logging.getLogger(__name__)

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
EMBEDDING_DIM = 384  # Dimension for all-MiniLM-L6-v2

# Get project root and create indexes directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_DIR = os.path.join(PROJECT_ROOT, "indexes")
os.makedirs(INDEX_DIR, exist_ok=True)

class EnhancedEmbeddingManager:
    def __init__(self):
        self.embedding_model = embedding_model
    
    def create_faiss_index_with_metadata(self, file_path: str, document_id: int, chunks: List[Dict[str, Any]]) -> int:
        """Create FAISS index with enhanced features"""
        start_time = time.time()
        
        try:
            # Extract chunk contents
            chunk_contents = [chunk["content"] for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(chunk_contents)
            embeddings = np.array(embeddings).astype('float32')
            
            # Create FAISS index
            index = faiss.IndexFlatIP(EMBEDDING_DIM)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            index.add(embeddings)
            
            # Save FAISS index
            index_file = os.path.join(INDEX_DIR, f"{os.path.basename(file_path)}.index")
            faiss.write_index(index, index_file)
            
            # Save chunk metadata as pickle for backward compatibility
            meta_file = index_file + ".meta"
            with open(meta_file, "wb") as f:
                pickle.dump(chunk_contents, f)
            
            duration = time.time() - start_time
            log_performance("FAISS_INDEX_CREATION", duration, 
                          chunks=len(chunks), file=os.path.basename(file_path))
            
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error creating FAISS index: {str(e)}")
            raise
    
    def search_similar_chunks(self, query: str, doc_paths: List[str], k: int = 3) -> List[Dict[str, Any]]:
        """Enhanced similarity search with scoring"""
        start_time = time.time()
        
        all_results = []
        query_embedding = self.embedding_model.encode([query])
        query_embedding = np.array(query_embedding).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        for doc_path in doc_paths:
            index_file = os.path.join(INDEX_DIR, f"{os.path.basename(doc_path)}.index")
            
            if not os.path.exists(index_file):
                continue
            
            try:
                # Load FAISS index
                index = faiss.read_index(index_file)
                
                # Load chunk metadata
                meta_file = index_file + ".meta"
                with open(meta_file, "rb") as f:
                    chunks = pickle.load(f)
                
                # Search
                scores, indices = index.search(query_embedding, min(k, len(chunks)))
                
                # Prepare results with metadata
                for score, idx in zip(scores[0], indices[0]):
                    if idx < len(chunks) and score > 0.1:  # Minimum similarity threshold
                        all_results.append({
                            "content": chunks[idx],
                            "score": float(score),
                            "document": os.path.basename(doc_path),
                            "chunk_index": int(idx)
                        })
                        
            except Exception as e:
                logger.error(f"Error searching in {doc_path}: {str(e)}")
                continue
        
        # Sort by relevance score
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        duration = time.time() - start_time
        log_performance("SIMILARITY_SEARCH", duration, 
                       documents=len(doc_paths), results=len(all_results))
        
        return all_results[:k]

# Create global instance
embedding_manager = EnhancedEmbeddingManager()

def create_faiss_index(file_path: str, document_id: int = None, chunking_strategy: str = "word") -> int:
    """Create FAISS index for a document with enhanced features"""
    from PyPDF2 import PdfReader
    
    try:
        # Extract text from PDF
        reader = PdfReader(file_path)
        full_text = "\n".join(page.extract_text() or "" for page in reader.pages)

        # Create chunks with metadata
        if isinstance(chunk_text(full_text), list) and len(chunk_text(full_text)) > 0:
            if isinstance(chunk_text(full_text)[0], dict):
                chunks = chunk_text(full_text, strategy=chunking_strategy)
            else:
                # Legacy format - convert to new format
                chunk_list = chunk_text(full_text)
                chunks = [{"content": chunk, "chunk_id": i, "word_count": len(chunk.split())} 
                         for i, chunk in enumerate(chunk_list)]
        else:
            chunks = chunk_text(full_text, strategy=chunking_strategy)
        
        # Create FAISS index
        if document_id:
            chunk_count = embedding_manager.create_faiss_index_with_metadata(file_path, document_id, chunks)
        else:
            # Fallback for backward compatibility
            chunk_contents = [chunk["content"] if isinstance(chunk, dict) else chunk for chunk in chunks]
            embeddings = embedding_model.encode(chunk_contents)
            embeddings = np.array(embeddings).astype('float32')
            
            index = faiss.IndexFlatIP(EMBEDDING_DIM)
            faiss.normalize_L2(embeddings)
            index.add(embeddings)
            
            index_file = os.path.join(INDEX_DIR, f"{os.path.basename(file_path)}.index")
            faiss.write_index(index, index_file)
            
            meta_file = index_file + ".meta"
            with open(meta_file, "wb") as f:
                pickle.dump(chunk_contents, f)
            
            chunk_count = len(chunks)
        
        logger.info(f"Created FAISS index for {os.path.basename(file_path)} with {chunk_count} chunks")
        return chunk_count
        
    except Exception as e:
        logger.error(f"Error creating FAISS index for {file_path}: {str(e)}")
        raise
