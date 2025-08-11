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
            
            # Check if we have any valid chunks
            if not chunk_contents or len(chunk_contents) == 0:
                logger.warning(f"No chunks to create index for file: {file_path}")
                return 0
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(chunk_contents)
            embeddings = np.array(embeddings).astype('float32')
            
            # Check if embeddings are valid
            if embeddings.size == 0 or len(embeddings.shape) < 2:
                logger.warning(f"Invalid embeddings for file: {file_path}")
                return 0
            
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
    """Create FAISS index for a document with enhanced features and metadata"""
    from app.file_processor import DocumentProcessor
    from app.utils import chunk_text_with_metadata
    
    try:
        # Extract text and metadata from PDF
        full_text, metadata = DocumentProcessor.extract_text_from_pdf(file_path)
        
        # Use enhanced chunking with page metadata
        page_contents = metadata.get('page_contents', [])
        if page_contents:
            chunks = chunk_text_with_metadata(page_contents)
        else:
            # Fallback to simple chunking
            from app.utils import chunk_text
            simple_chunks = chunk_text(full_text, strategy=chunking_strategy)
            chunks = simple_chunks
        
        # Create FAISS index
        if document_id and len(chunks) > 0:
            chunk_count = embedding_manager.create_faiss_index_with_metadata(file_path, document_id, chunks)
        else:
            # Fallback for backward compatibility
            chunk_contents = []
            for chunk in chunks:
                if isinstance(chunk, dict):
                    chunk_contents.append(chunk.get('content', str(chunk)))
                else:
                    chunk_contents.append(str(chunk))
            
            if not chunk_contents:
                logger.warning(f"No valid chunks to index for {file_path}")
                return 0
            
            embeddings = embedding_model.encode(chunk_contents)
            embeddings = np.array(embeddings).astype('float32')
            
            index = faiss.IndexFlatIP(EMBEDDING_DIM)
            faiss.normalize_L2(embeddings)
            index.add(embeddings)
            
            index_file = os.path.join(INDEX_DIR, f"{os.path.basename(file_path)}.index")
            faiss.write_index(index, index_file)
            
            meta_file = index_file + ".meta"
            with open(meta_file, "wb") as f:
                pickle.dump(chunks, f)  # Store full chunk objects with metadata
            
            chunk_count = len(chunks)
        
        logger.info(f"Created FAISS index for {os.path.basename(file_path)} with {chunk_count} chunks")
        return chunk_count
        
    except Exception as e:
        logger.error(f"Error creating FAISS index for {file_path}: {str(e)}")
        raise
