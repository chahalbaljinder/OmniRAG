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
        """Create FAISS index with enhanced features and source metadata"""
        start_time = time.time()
        
        try:
            # Extract chunk contents and prepare enhanced metadata
            chunk_contents = []
            chunk_metadata = []
            
            for i, chunk in enumerate(chunks):
                content = chunk["content"] if isinstance(chunk, dict) else chunk
                chunk_contents.append(content)
                
                # Create enhanced metadata for each chunk
                chunk_meta = {
                    "content": content,
                    "chunk_id": int(i),
                    "document_id": int(document_id) if document_id is not None else None,
                    "source_file": os.path.basename(file_path),
                    "chunk_index": int(i),
                    "word_count": int(len(content.split()) if content else 0),
                    "char_count": int(len(content) if content else 0)
                }
                
                # Add page information if available in chunk
                if isinstance(chunk, dict):
                    chunk_meta.update({
                        "page_number": chunk.get("page_number"),
                        "start_char": chunk.get("start_char"),
                        "end_char": chunk.get("end_char"),
                        "section": chunk.get("section"),
                        "metadata": chunk.get("metadata", {})
                    })
                    
                    # Add comprehensive case metadata if available
                    case_fields = [
                        'Case_Name', 'Case_No', 'Judges', 'Order_Date', 
                        'Adjudication_Deadline', 'Appellant', 'Appellant_Advocate',
                        'Respondents', 'Respondent_Advocates', 'Court', 'Filing_Date'
                    ]
                    
                    for field in case_fields:
                        if field in chunk:
                            chunk_meta[field] = chunk[field]
                
                chunk_metadata.append(chunk_meta)
            
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
            
            # Save enhanced chunk metadata
            meta_file = index_file + ".meta"
            with open(meta_file, "wb") as f:
                pickle.dump(chunk_metadata, f)
                
            # Also save legacy format for backward compatibility
            legacy_meta_file = index_file + ".legacy.meta"
            with open(legacy_meta_file, "wb") as f:
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

def create_global_faiss_index():
    """Create or update the global FAISS index from all individual document indexes"""
    try:
        # Get project root and create faiss_index directory
        faiss_index_dir = os.path.join(PROJECT_ROOT, "faiss_index")
        os.makedirs(faiss_index_dir, exist_ok=True)
        
        global_index_path = os.path.join(faiss_index_dir, "index.faiss")
        global_metadata_path = os.path.join(faiss_index_dir, "index.pkl")
        
        all_embeddings = []
        all_metadata = []
        
        # Scan all individual indexes
        for filename in os.listdir(INDEX_DIR):
            if filename.endswith(".index"):
                index_file = os.path.join(INDEX_DIR, filename)
                meta_file = index_file + ".meta"
                
                if os.path.exists(meta_file):
                    try:
                        # Load individual index
                        index = faiss.read_index(index_file)
                        
                        # Load metadata
                        with open(meta_file, "rb") as f:
                            metadata = pickle.load(f)
                        
                        # Clean metadata to ensure JSON serializable types
                        cleaned_metadata = []
                        for item in metadata:
                            if isinstance(item, dict):
                                cleaned_item = {
                                    "content": str(item.get("content", "")),
                                    "chunk_id": int(item.get("chunk_id", 0)),
                                    "document_id": int(item.get("document_id", 0)) if item.get("document_id") is not None else None,
                                    "source_file": str(item.get("source_file", filename.replace(".index", ""))),
                                    "chunk_index": int(item.get("chunk_index", 0)),
                                    "word_count": int(item.get("word_count", 0)),
                                    "char_count": int(item.get("char_count", 0)),
                                    "page_number": item.get("page_number", "N/A"),
                                    "start_char": item.get("start_char"),
                                    "end_char": item.get("end_char"),
                                    "section": item.get("section"),
                                }
                                
                                # Add comprehensive case metadata fields
                                case_fields = [
                                    'Case_Name', 'Case_No', 'Judges', 'Order_Date', 
                                    'Adjudication_Deadline', 'Appellant', 'Appellant_Advocate',
                                    'Respondents', 'Respondent_Advocates', 'Court', 'Filing_Date'
                                ]
                                
                                for field in case_fields:
                                    if field in item:
                                        cleaned_item[field] = item[field]
                                
                                # Add any additional metadata fields that might exist
                                if "metadata" in item and isinstance(item["metadata"], dict):
                                    cleaned_item.update(item["metadata"])
                                    
                                cleaned_metadata.append(cleaned_item)
                            else:
                                # Handle legacy format - just strings
                                cleaned_metadata.append({
                                    "content": str(item),
                                    "chunk_id": len(cleaned_metadata),
                                    "document_id": None,
                                    "source_file": filename.replace(".index", ""),
                                    "chunk_index": len(cleaned_metadata),
                                    "word_count": len(str(item).split()),
                                    "char_count": len(str(item)),
                                    "page_number": "N/A"
                                })
                        
                        # Extract embeddings from the index
                        embeddings = index.reconstruct_n(0, index.ntotal)
                        
                        all_embeddings.append(embeddings)
                        all_metadata.extend(cleaned_metadata)
                        
                    except Exception as e:
                        logger.error(f"Error processing {filename}: {str(e)}")
                        continue
        
        if all_embeddings:
            # Combine all embeddings
            combined_embeddings = np.vstack(all_embeddings)
            
            # Create global index
            global_index = faiss.IndexFlatIP(EMBEDDING_DIM)
            faiss.normalize_L2(combined_embeddings)
            global_index.add(combined_embeddings)
            
            # Save global index
            faiss.write_index(global_index, global_index_path)
            
            # Save global metadata
            with open(global_metadata_path, "wb") as f:
                pickle.dump(all_metadata, f)
            
            logger.info(f"Created global FAISS index with {len(all_metadata)} chunks from {len(all_embeddings)} documents")
            return len(all_metadata)
        else:
            logger.warning("No individual indexes found to create global index")
            return 0
            
    except Exception as e:
        logger.error(f"Error creating global FAISS index: {str(e)}")
        raise

def create_faiss_index(file_path: str, document_id: int = None, chunking_strategy: str = "word") -> int:
    """Create FAISS index for a document with enhanced features"""
    from PyPDF2 import PdfReader
    from app.file_processor import DocumentProcessor
    
    try:
        # Extract text and metadata from PDF
        text, pdf_metadata = DocumentProcessor.extract_text_from_pdf(file_path)
        
        # Create chunks with metadata
        if isinstance(chunk_text(text), list) and len(chunk_text(text)) > 0:
            if isinstance(chunk_text(text)[0], dict):
                chunks = chunk_text(text, strategy=chunking_strategy)
            else:
                # Legacy format - convert to new format
                chunk_list = chunk_text(text)
                chunks = [{"content": chunk, "chunk_id": i, "word_count": len(chunk.split())} 
                         for i, chunk in enumerate(chunk_list)]
        else:
            chunks = chunk_text(text, strategy=chunking_strategy)
        
        # Add case metadata to each chunk
        case_metadata = pdf_metadata.copy()  # This includes the extracted case metadata
        for chunk in chunks:
            if isinstance(chunk, dict):
                # Add case metadata to each chunk
                chunk.update(case_metadata)
        
        # Create FAISS index - ALWAYS use enhanced metadata method
        chunk_count = embedding_manager.create_faiss_index_with_metadata(file_path, document_id or 0, chunks)
        
        logger.info(f"Created FAISS index for {os.path.basename(file_path)} with {chunk_count} chunks")
        return chunk_count
        
    except Exception as e:
        logger.error(f"Error creating FAISS index for {file_path}: {str(e)}")
        raise
