# app/cache.py - Caching system for RAG pipeline

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.database import get_db, QueryCache
from app.config import settings

class CacheManager:
    """Manages query caching with database persistence"""
    
    def __init__(self):
        self.cache_ttl = settings.cache_ttl
        self.enabled = settings.enable_caching
    
    def _generate_query_hash(self, query: str, document_ids: List[int], k: int = 3) -> str:
        """Generate hash for query + document combination"""
        cache_key = {
            "query": query.lower().strip(),
            "documents": sorted(document_ids),
            "k": k
        }
        return hashlib.sha256(json.dumps(cache_key, sort_keys=True).encode()).hexdigest()
    
    def _generate_documents_hash(self, document_ids: List[int]) -> str:
        """Generate hash for document set"""
        return hashlib.sha256(json.dumps(sorted(document_ids)).encode()).hexdigest()
    
    def get_cached_response(self, query: str, document_ids: List[int], k: int = 3, db: Session = None) -> Optional[str]:
        """Get cached response if available and valid"""
        if not self.enabled or not db:
            return None
        
        try:
            query_hash = self._generate_query_hash(query, document_ids, k)
            
            cache_entry = db.query(QueryCache).filter(
                QueryCache.query_hash == query_hash,
                QueryCache.expires_at > datetime.utcnow()
            ).first()
            
            if cache_entry:
                # Update hit count
                cache_entry.hit_count += 1
                db.commit()
                return cache_entry.response_text
            
            return None
            
        except Exception as e:
            print(f"Cache retrieval error: {e}")
            return None
    
    def cache_response(self, query: str, response: str, document_ids: List[int], k: int = 3, db: Session = None):
        """Cache query response"""
        if not self.enabled or not db:
            return
        
        try:
            query_hash = self._generate_query_hash(query, document_ids, k)
            documents_hash = self._generate_documents_hash(document_ids)
            expires_at = datetime.utcnow() + timedelta(seconds=self.cache_ttl)
            
            # Remove existing cache entry if any
            existing = db.query(QueryCache).filter(QueryCache.query_hash == query_hash).first()
            if existing:
                db.delete(existing)
            
            # Create new cache entry
            cache_entry = QueryCache(
                query_hash=query_hash,
                query_text=query,
                response_text=response,
                documents_hash=documents_hash,
                expires_at=expires_at
            )
            
            db.add(cache_entry)
            db.commit()
            
        except Exception as e:
            print(f"Cache storage error: {e}")
            db.rollback()
    
    def invalidate_document_cache(self, document_ids: List[int], db: Session = None):
        """Invalidate cache entries that used specific documents"""
        if not self.enabled or not db:
            return
        
        try:
            documents_hash = self._generate_documents_hash(document_ids)
            
            # Delete cache entries that used these documents
            db.query(QueryCache).filter(QueryCache.documents_hash == documents_hash).delete()
            db.commit()
            
        except Exception as e:
            print(f"Cache invalidation error: {e}")
            db.rollback()
    
    def clear_expired_cache(self, db: Session = None):
        """Clear expired cache entries"""
        if not db:
            return
        
        try:
            db.query(QueryCache).filter(QueryCache.expires_at <= datetime.utcnow()).delete()
            db.commit()
        except Exception as e:
            print(f"Cache cleanup error: {e}")
            db.rollback()
    
    def get_cache_stats(self, db: Session = None) -> Dict[str, Any]:
        """Get cache statistics"""
        if not db:
            return {}
        
        try:
            total_entries = db.query(QueryCache).count()
            expired_entries = db.query(QueryCache).filter(QueryCache.expires_at <= datetime.utcnow()).count()
            total_hits = db.query(QueryCache).with_entities(
                db.func.sum(QueryCache.hit_count)
            ).scalar() or 0
            
            return {
                "total_entries": total_entries,
                "active_entries": total_entries - expired_entries,
                "expired_entries": expired_entries,
                "total_hits": total_hits,
                "cache_enabled": self.enabled
            }
            
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {"error": str(e)}

class InMemoryCache:
    """Simple in-memory cache with TTL"""
    
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set item in cache"""
        if len(self.cache) >= self.max_size:
            # Remove oldest item
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[key] = (value, time.time())
    
    def delete(self, key: str):
        """Delete item from cache"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        valid_items = sum(1 for _, timestamp in self.cache.values() if current_time - timestamp < self.ttl)
        
        return {
            "total_items": len(self.cache),
            "valid_items": valid_items,
            "expired_items": len(self.cache) - valid_items,
            "max_size": self.max_size,
            "ttl": self.ttl
        }

# Global in-memory cache instances (after class definition)
embedding_cache = InMemoryCache(max_size=500, ttl=1800)  # 30 minutes
document_cache = InMemoryCache(max_size=100, ttl=600)    # 10 minutes

# Global cache manager instance
cache_manager = CacheManager()

# Helper functions for API compatibility
def query_cache(query: str, document_ids: List[int], k: int = 3) -> Optional[Dict[str, Any]]:
    """Query cache for results"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        return cache_manager.get_query_result(query, document_ids, k, db)
    finally:
        db.close()

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return {
        "embedding_cache": embedding_cache.stats(),
        "document_cache": document_cache.stats(),
        "cache_enabled": cache_manager.enabled,
        "cache_ttl": cache_manager.cache_ttl
    }

def clear_all_cache():
    """Clear all caches"""
    embedding_cache.clear()
    document_cache.clear()
