# app/hybrid_search.py - Hybrid search implementation

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
import faiss
import logging
from app.database import Document, Chunk
from app.cache import embedding_cache

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Search result with scores and metadata"""
    chunk_id: int
    document_id: int
    text: str
    semantic_score: float
    keyword_score: float
    hybrid_score: float
    metadata: Dict[str, Any]

class HybridSearchEngine:
    """Hybrid search combining semantic and keyword search"""
    
    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2"):
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        self.faiss_index = None
        self.chunk_texts = []
        self.chunk_metadata = []
        self.tfidf_matrix = None
        self.is_fitted = False
        
    def build_index(self, chunks: List[Tuple[str, Dict[str, Any]]]):
        """Build both semantic and keyword indexes"""
        logger.info(f"Building hybrid search index for {len(chunks)} chunks")
        
        # Extract texts and metadata
        self.chunk_texts = [chunk[0] for chunk in chunks]
        self.chunk_metadata = [chunk[1] for chunk in chunks]
        
        # Build semantic index (FAISS)
        embeddings = self._get_embeddings(self.chunk_texts)
        dimension = embeddings.shape[1]
        
        self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.faiss_index.add(embeddings)
        
        # Build keyword index (TF-IDF)
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.chunk_texts)
        
        self.is_fitted = True
        logger.info("Hybrid search index built successfully")
    
    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings with caching"""
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache for existing embeddings
        for i, text in enumerate(texts):
            cached_embedding = embedding_cache.get_embedding(text)
            if cached_embedding is not None:
                embeddings.append(cached_embedding)
            else:
                embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            logger.info(f"Generating embeddings for {len(uncached_texts)} uncached texts")
            new_embeddings = self.embedding_model.encode(uncached_texts, convert_to_numpy=True)
            
            # Cache new embeddings and update the list
            for idx, embedding in zip(uncached_indices, new_embeddings):
                embedding_cache.set_embedding(uncached_texts[uncached_indices.index(idx)], embedding.tolist())
                embeddings[idx] = embedding
        
        return np.array(embeddings)
    
    def semantic_search(self, query: str, k: int = 10) -> List[Tuple[int, float]]:
        """Perform semantic search using FAISS"""
        if not self.is_fitted:
            raise ValueError("Index not built. Call build_index first.")
        
        # Get query embedding
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.faiss_index.search(query_embedding, k)
        
        # Return (index, score) pairs
        return [(int(indices[0][i]), float(scores[0][i])) for i in range(len(indices[0]))]
    
    def keyword_search(self, query: str, k: int = 10) -> List[Tuple[int, float]]:
        """Perform keyword search using TF-IDF"""
        if not self.is_fitted:
            raise ValueError("Index not built. Call build_index first.")
        
        # Transform query
        query_vector = self.tfidf_vectorizer.transform([query])
        
        # Calculate cosine similarity
        scores = (self.tfidf_matrix * query_vector.T).toarray().flatten()
        
        # Get top k results
        top_indices = np.argsort(scores)[::-1][:k]
        
        return [(int(idx), float(scores[idx])) for idx in top_indices if scores[idx] > 0]
    
    def hybrid_search(self, query: str, k: int = 10, 
                     semantic_weight: float = 0.7, 
                     keyword_weight: float = 0.3) -> List[SearchResult]:
        """Perform hybrid search combining semantic and keyword search"""
        if not self.is_fitted:
            raise ValueError("Index not built. Call build_index first.")
        
        # Perform both searches
        semantic_results = self.semantic_search(query, k * 2)  # Get more for better combination
        keyword_results = self.keyword_search(query, k * 2)
        
        # Combine results
        combined_scores = {}
        
        # Add semantic scores
        for idx, score in semantic_results:
            combined_scores[idx] = {
                'semantic_score': score,
                'keyword_score': 0.0,
                'text': self.chunk_texts[idx],
                'metadata': self.chunk_metadata[idx]
            }
        
        # Add keyword scores
        for idx, score in keyword_results:
            if idx in combined_scores:
                combined_scores[idx]['keyword_score'] = score
            else:
                combined_scores[idx] = {
                    'semantic_score': 0.0,
                    'keyword_score': score,
                    'text': self.chunk_texts[idx],
                    'metadata': self.chunk_metadata[idx]
                }
        
        # Calculate hybrid scores and create results
        results = []
        for idx, scores in combined_scores.items():
            hybrid_score = (semantic_weight * scores['semantic_score'] + 
                          keyword_weight * scores['keyword_score'])
            
            result = SearchResult(
                chunk_id=scores['metadata'].get('chunk_id', idx),
                document_id=scores['metadata'].get('document_id', 0),
                text=scores['text'],
                semantic_score=scores['semantic_score'],
                keyword_score=scores['keyword_score'],
                hybrid_score=hybrid_score,
                metadata=scores['metadata']
            )
            results.append(result)
        
        # Sort by hybrid score and return top k
        results.sort(key=lambda x: x.hybrid_score, reverse=True)
        return results[:k]
    
    def rerank_results(self, query: str, results: List[SearchResult], 
                      rerank_model: Optional[str] = None) -> List[SearchResult]:
        """Re-rank results using a more sophisticated model"""
        if not rerank_model:
            # Simple re-ranking based on query-text similarity and result diversity
            return self._simple_rerank(query, results)
        
        # Could implement more sophisticated re-ranking here
        return results
    
    def _simple_rerank(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """Simple re-ranking to promote diversity and relevance"""
        if len(results) <= 3:
            return results
        
        reranked = []
        used_documents = set()
        
        # First pass: pick best result from each document
        for result in results:
            if result.document_id not in used_documents:
                reranked.append(result)
                used_documents.add(result.document_id)
        
        # Second pass: add remaining results
        remaining_slots = len(results) - len(reranked)
        for result in results:
            if len(reranked) >= len(results):
                break
            if result not in reranked:
                reranked.append(result)
        
        return reranked
    
    def explain_search(self, query: str, result: SearchResult) -> Dict[str, Any]:
        """Explain why a particular result was returned"""
        return {
            'query': query,
            'result_id': result.chunk_id,
            'semantic_score': result.semantic_score,
            'keyword_score': result.keyword_score,
            'hybrid_score': result.hybrid_score,
            'explanation': {
                'semantic_relevance': 'High' if result.semantic_score > 0.5 else 'Medium' if result.semantic_score > 0.3 else 'Low',
                'keyword_match': 'High' if result.keyword_score > 0.1 else 'Medium' if result.keyword_score > 0.05 else 'Low',
                'overall_relevance': 'High' if result.hybrid_score > 0.4 else 'Medium' if result.hybrid_score > 0.2 else 'Low'
            }
        }

# Global hybrid search engine instance
hybrid_search_engine = HybridSearchEngine()

def initialize_hybrid_search(chunks: List[Tuple[str, Dict[str, Any]]]):
    """Initialize the global hybrid search engine"""
    hybrid_search_engine.build_index(chunks)

def search_documents(query: str, k: int = 10, 
                    search_type: str = "hybrid",
                    semantic_weight: float = 0.7,
                    keyword_weight: float = 0.3) -> List[SearchResult]:
    """Search documents using specified method"""
    if search_type == "semantic":
        results = hybrid_search_engine.semantic_search(query, k)
        return [SearchResult(
            chunk_id=idx,
            document_id=hybrid_search_engine.chunk_metadata[idx].get('document_id', 0),
            text=hybrid_search_engine.chunk_texts[idx],
            semantic_score=score,
            keyword_score=0.0,
            hybrid_score=score,
            metadata=hybrid_search_engine.chunk_metadata[idx]
        ) for idx, score in results]
    
    elif search_type == "keyword":
        results = hybrid_search_engine.keyword_search(query, k)
        return [SearchResult(
            chunk_id=idx,
            document_id=hybrid_search_engine.chunk_metadata[idx].get('document_id', 0),
            text=hybrid_search_engine.chunk_texts[idx],
            semantic_score=0.0,
            keyword_score=score,
            hybrid_score=score,
            metadata=hybrid_search_engine.chunk_metadata[idx]
        ) for idx, score in results]
    
    else:  # hybrid
        return hybrid_search_engine.hybrid_search(query, k, semantic_weight, keyword_weight)
