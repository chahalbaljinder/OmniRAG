# app/search.py - Advanced search capabilities including hybrid search

import re
import math
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import faiss

from app.database import DocumentChunk
from app.embedding import embedding_model
from app.config import settings

class KeywordSearcher:
    """BM25-based keyword search"""
    
    def __init__(self):
        self.k1 = 1.5  # Term frequency saturation point
        self.b = 0.75  # Length normalization parameter
        self.vectorizer = None
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.corpus = []
        self.idf_scores = {}
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for keyword search"""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def build_index(self, documents: List[str]):
        """Build BM25 index from documents"""
        self.corpus = [self.preprocess_text(doc) for doc in documents]
        
        # Calculate document lengths
        self.doc_lengths = [len(doc.split()) for doc in self.corpus]
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0
        
        # Build TF-IDF vectorizer for IDF scores
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)
        tfidf_matrix = self.vectorizer.fit_transform(self.corpus)
        
        # Extract IDF scores
        feature_names = self.vectorizer.get_feature_names_out()
        idf_values = self.vectorizer.idf_
        self.idf_scores = dict(zip(feature_names, idf_values))
    
    def get_bm25_score(self, query: str, doc_idx: int) -> float:
        """Calculate BM25 score for a document"""
        if not self.corpus or doc_idx >= len(self.corpus):
            return 0.0
        
        query_terms = self.preprocess_text(query).split()
        doc_terms = self.corpus[doc_idx].split()
        doc_length = self.doc_lengths[doc_idx]
        
        score = 0.0
        term_frequencies = Counter(doc_terms)
        
        for term in query_terms:
            if term in term_frequencies:
                tf = term_frequencies[term]
                idf = self.idf_scores.get(term, 0)
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
                score += idf * (numerator / denominator)
        
        return score
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """Search documents using BM25"""
        if not self.corpus:
            return []
        
        scores = []
        for i in range(len(self.corpus)):
            score = self.get_bm25_score(query, i)
            scores.append((i, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

class SemanticSearcher:
    """Embedding-based semantic search"""
    
    def __init__(self):
        self.index = None
        self.chunk_ids = []
        self.embeddings = []
    
    def build_index(self, chunks: List[DocumentChunk]):
        """Build FAISS index for semantic search"""
        if not chunks:
            return
        
        self.chunk_ids = [chunk.id for chunk in chunks]
        
        # Get embeddings for all chunks
        chunk_texts = [chunk.content for chunk in chunks]
        self.embeddings = embedding_model.encode(chunk_texts)
        
        # Build FAISS index
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.embeddings)
        self.index.add(self.embeddings)
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """Search chunks using semantic similarity"""
        if not self.index:
            return []
        
        # Encode query
        query_embedding = embedding_model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, top_k)
        
        # Return chunk IDs and scores
        results = []
        for i, (idx, score) in enumerate(zip(indices[0], scores[0])):
            if idx < len(self.chunk_ids):
                results.append((self.chunk_ids[idx], float(score)))
        
        return results

class HybridSearcher:
    """Combines keyword and semantic search"""
    
    def __init__(self, keyword_weight: float = 0.3, semantic_weight: float = 0.7):
        self.keyword_searcher = KeywordSearcher()
        self.semantic_searcher = SemanticSearcher()
        self.keyword_weight = keyword_weight
        self.semantic_weight = semantic_weight
        self.chunks = []
    
    def build_index(self, chunks: List[DocumentChunk]):
        """Build both keyword and semantic indexes"""
        self.chunks = chunks
        
        # Build keyword index
        chunk_texts = [chunk.content for chunk in chunks]
        self.keyword_searcher.build_index(chunk_texts)
        
        # Build semantic index
        self.semantic_searcher.build_index(chunks)
    
    def search(self, query: str, top_k: int = 10, strategy: str = "hybrid") -> List[Tuple[int, float, str]]:
        """
        Search using specified strategy
        
        Args:
            query: Search query
            top_k: Number of results to return
            strategy: "hybrid", "keyword", "semantic"
            
        Returns:
            List of (chunk_id, combined_score, search_type)
        """
        if strategy == "keyword":
            keyword_results = self.keyword_searcher.search(query, top_k)
            return [(self.chunks[idx].id, score, "keyword") for idx, score in keyword_results]
        
        elif strategy == "semantic":
            semantic_results = self.semantic_searcher.search(query, top_k)
            return [(chunk_id, score, "semantic") for chunk_id, score in semantic_results]
        
        else:  # hybrid
            return self._hybrid_search(query, top_k)
    
    def _hybrid_search(self, query: str, top_k: int) -> List[Tuple[int, float, str]]:
        """Perform hybrid search combining keyword and semantic results"""
        # Get results from both methods
        keyword_results = self.keyword_searcher.search(query, top_k * 2)
        semantic_results = self.semantic_searcher.search(query, top_k * 2)
        
        # Normalize scores to [0, 1] range
        keyword_scores = self._normalize_scores([score for _, score in keyword_results])
        semantic_scores = self._normalize_scores([score for _, score in semantic_results])
        
        # Create score maps
        keyword_score_map = {}
        for i, (idx, _) in enumerate(keyword_results):
            if idx < len(self.chunks):
                chunk_id = self.chunks[idx].id
                keyword_score_map[chunk_id] = keyword_scores[i]
        
        semantic_score_map = {}
        for i, (chunk_id, _) in enumerate(semantic_results):
            semantic_score_map[chunk_id] = semantic_scores[i]
        
        # Combine scores
        combined_scores = {}
        all_chunk_ids = set(keyword_score_map.keys()) | set(semantic_score_map.keys())
        
        for chunk_id in all_chunk_ids:
            keyword_score = keyword_score_map.get(chunk_id, 0)
            semantic_score = semantic_score_map.get(chunk_id, 0)
            
            # Weighted combination
            combined_score = (
                self.keyword_weight * keyword_score +
                self.semantic_weight * semantic_score
            )
            combined_scores[chunk_id] = combined_score
        
        # Sort by combined score
        sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [(chunk_id, score, "hybrid") for chunk_id, score in sorted_results[:top_k]]
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to [0, 1] range using min-max normalization"""
        if not scores:
            return []
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [1.0] * len(scores)
        
        return [(score - min_score) / (max_score - min_score) for score in scores]

class QueryExpander:
    """Expand queries with synonyms and related terms"""
    
    def __init__(self):
        # Simple synonym dictionary - in production, use WordNet or word embeddings
        self.synonyms = {
            "algorithm": ["method", "procedure", "technique", "approach"],
            "model": ["framework", "system", "architecture"],
            "data": ["information", "dataset", "content"],
            "analysis": ["examination", "evaluation", "study"],
            "performance": ["efficiency", "effectiveness", "speed"],
            "research": ["study", "investigation", "analysis"],
            "method": ["approach", "technique", "procedure"],
            "result": ["outcome", "finding", "conclusion"],
            "problem": ["issue", "challenge", "difficulty"],
            "solution": ["answer", "resolution", "approach"]
        }
    
    def expand_query(self, query: str, max_expansions: int = 2) -> str:
        """Expand query with synonyms"""
        words = query.lower().split()
        expanded_words = list(words)
        
        for word in words:
            if word in self.synonyms:
                # Add up to max_expansions synonyms
                synonyms = self.synonyms[word][:max_expansions]
                expanded_words.extend(synonyms)
        
        return " ".join(expanded_words)
    
    def extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms from query"""
        # Remove common stop words and extract meaningful terms
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "have",
            "has", "had", "do", "does", "did", "will", "would", "could", "should",
            "what", "how", "when", "where", "why", "who", "which"
        }
        
        words = re.findall(r'\b\w+\b', query.lower())
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        return key_terms

class ReRanker:
    """Re-rank search results based on additional criteria"""
    
    def __init__(self):
        self.diversity_weight = 0.2
        self.freshness_weight = 0.1
        self.relevance_weight = 0.7
    
    def rerank_results(self, 
                      results: List[Tuple[int, float, str]], 
                      chunks: List[DocumentChunk],
                      query: str) -> List[Tuple[int, float, str]]:
        """Re-rank results considering diversity and other factors"""
        if not results:
            return results
        
        # Create chunk lookup
        chunk_lookup = {chunk.id: chunk for chunk in chunks}
        
        reranked_results = []
        used_documents = set()
        
        for chunk_id, score, search_type in results:
            chunk = chunk_lookup.get(chunk_id)
            if not chunk:
                continue
            
            # Calculate diversity penalty
            diversity_penalty = 0
            if chunk.document_id in used_documents:
                diversity_penalty = 0.3  # Penalty for same document
            
            # Calculate adjusted score
            adjusted_score = score * (1 - diversity_penalty * self.diversity_weight)
            
            reranked_results.append((chunk_id, adjusted_score, search_type))
            used_documents.add(chunk.document_id)
        
        # Sort by adjusted score
        reranked_results.sort(key=lambda x: x[1], reverse=True)
        return reranked_results

# Global search components
hybrid_searcher = HybridSearcher()
query_expander = QueryExpander()
reranker = ReRanker()
