# app/async_processing.py - Asynchronous processing for file uploads and heavy tasks

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
import json
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session

from app.database import get_db, Document
from app.config import settings

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    name: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for JSON serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data

class TaskManager:
    """Manages asynchronous tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.max_concurrent_tasks = 5
        self.task_timeout = 3600  # 1 hour
        
    def create_task(self, name: str, func: Callable, *args, **kwargs) -> str:
        """Create a new asynchronous task"""
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            name=name,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            metadata=kwargs.pop('metadata', {})
        )
        
        self.tasks[task_id] = task
        
        # Start task if we have capacity
        if len(self.running_tasks) < self.max_concurrent_tasks:
            self._start_task(task_id, func, *args, **kwargs)
        
        return task_id
    
    def _start_task(self, task_id: str, func: Callable, *args, **kwargs):
        """Start executing a task"""
        task = self.tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        # Create asyncio task
        async_task = asyncio.create_task(self._execute_task(task_id, func, *args, **kwargs))
        self.running_tasks[task_id] = async_task
    
    async def _execute_task(self, task_id: str, func: Callable, *args, **kwargs):
        """Execute a task with error handling"""
        task = self.tasks[task_id]
        
        try:
            # Set up progress callback if supported
            if 'progress_callback' in kwargs:
                del kwargs['progress_callback']
                kwargs['progress_callback'] = lambda p: self._update_progress(task_id, p)
            
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            task.progress = 100.0
            
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            task.error = "Task was cancelled"
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error = str(e)
            
        finally:
            # Clean up
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            # Start next pending task if any
            self._start_next_pending_task()
    
    def _update_progress(self, task_id: str, progress: float):
        """Update task progress"""
        if task_id in self.tasks:
            self.tasks[task_id].progress = min(100.0, max(0.0, progress))
    
    def _start_next_pending_task(self):
        """Start the next pending task if we have capacity"""
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            return
        
        # Find next pending task
        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.PENDING:
                # We need to store the function and args with the task
                # For now, we'll skip this complexity
                break
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks"""
        return list(self.tasks.values())
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        if task_id in self.running_tasks:
            async_task = self.running_tasks[task_id]
            async_task.cancel()
            return True
        elif task_id in self.tasks and self.tasks[task_id].status == TaskStatus.PENDING:
            self.tasks[task_id].status = TaskStatus.CANCELLED
            self.tasks[task_id].completed_at = datetime.utcnow()
            return True
        return False
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task.completed_at and task.completed_at < cutoff_time):
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]

# Global task manager
task_manager = TaskManager()

class AsyncDocumentProcessor:
    """Asynchronous document processing"""
    
    @staticmethod
    async def process_document_async(file_path: str, document_id: int, progress_callback: Callable = None) -> Dict[str, Any]:
        """Process document asynchronously with progress updates"""
        try:
            if progress_callback:
                progress_callback(10)
            
            # Import here to avoid circular imports
            from app.file_processor import DocumentProcessor
            from app.embedding import create_faiss_index
            
            # Extract text and metadata
            if progress_callback:
                progress_callback(30)
            
            text, metadata = DocumentProcessor.extract_text_from_pdf(file_path)
            
            if progress_callback:
                progress_callback(60)
            
            # Create embeddings
            chunk_count = create_faiss_index(file_path, document_id)
            
            if progress_callback:
                progress_callback(90)
            
            # Update database
            from app.database import SessionLocal
            db = SessionLocal()
            
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.chunk_count = chunk_count
                document.file_metadata = json.dumps(metadata)
                db.commit()
            
            db.close()
            
            if progress_callback:
                progress_callback(100)
            
            return {
                "document_id": document_id,
                "chunks_created": chunk_count,
                "metadata": metadata
            }
            
        except Exception as e:
            raise Exception(f"Document processing failed: {str(e)}")

class AsyncQueryProcessor:
    """Asynchronous query processing for complex queries"""
    
    @staticmethod
    async def process_complex_query(query: str, document_ids: List[int], search_type: str = "hybrid", progress_callback: Callable = None) -> Dict[str, Any]:
        """Process complex query asynchronously"""
        try:
            if progress_callback:
                progress_callback(10)
            
            # Import here to avoid circular imports
            from app.search import hybrid_searcher, query_expander
            from app.rag import get_answer_advanced
            from app.database import SessionLocal, DocumentChunk
            
            # Expand query if needed
            if progress_callback:
                progress_callback(20)
            
            expanded_query = query_expander.expand_query(query)
            
            # Get relevant chunks
            if progress_callback:
                progress_callback(40)
            
            db = SessionLocal()
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id.in_(document_ids)
            ).all()
            
            # Build search index
            if progress_callback:
                progress_callback(60)
            
            hybrid_searcher.build_index(chunks)
            
            # Perform search
            search_results = hybrid_searcher.search(expanded_query, top_k=10, strategy=search_type)
            
            if progress_callback:
                progress_callback(80)
            
            # Generate answer (this would be implemented in rag.py)
            # answer = get_answer_advanced(query, search_results, chunks)
            answer = f"Advanced answer for: {query}"  # Placeholder
            
            db.close()
            
            if progress_callback:
                progress_callback(100)
            
            return {
                "query": query,
                "expanded_query": expanded_query,
                "answer": answer,
                "search_results_count": len(search_results),
                "search_type": search_type
            }
            
        except Exception as e:
            raise Exception(f"Query processing failed: {str(e)}")

class BatchProcessor:
    """Process multiple documents in batches"""
    
    @staticmethod
    async def process_document_batch(file_paths: List[str], batch_size: int = 3, progress_callback: Callable = None) -> List[Dict[str, Any]]:
        """Process multiple documents in batches"""
        results = []
        total_files = len(file_paths)
        
        for i in range(0, total_files, batch_size):
            batch = file_paths[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = []
            for file_path in batch:
                # This would need to be implemented properly with document creation
                task = AsyncDocumentProcessor.process_document_async(file_path, 0)  # Placeholder
                batch_tasks.append(task)
            
            # Wait for batch completion
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    results.append({
                        "file_path": batch[j],
                        "status": "error",
                        "error": str(result)
                    })
                else:
                    results.append({
                        "file_path": batch[j],
                        "status": "success",
                        "result": result
                    })
            
            # Update progress
            if progress_callback:
                progress = ((i + len(batch)) / total_files) * 100
                progress_callback(progress)
        
        return results

# Utility functions for async processing
async def schedule_document_processing(file_path: str, document_id: int) -> str:
    """Schedule document processing as async task"""
    task_id = task_manager.create_task(
        f"process_document_{document_id}",
        AsyncDocumentProcessor.process_document_async,
        file_path,
        document_id,
        metadata={"document_id": document_id, "file_path": file_path}
    )
    return task_id

async def schedule_complex_query(query: str, document_ids: List[int], search_type: str = "hybrid") -> str:
    """Schedule complex query processing as async task"""
    task_id = task_manager.create_task(
        f"complex_query_{len(document_ids)}_docs",
        AsyncQueryProcessor.process_complex_query,
        query,
        document_ids,
        search_type,
        metadata={"query": query[:100], "document_count": len(document_ids)}
    )
    return task_id

# Background task for cleanup
async def background_cleanup_task():
    """Background task to cleanup old tasks and cache"""
    while True:
        try:
            # Cleanup old tasks
            task_manager.cleanup_old_tasks()
            
            # Cleanup expired cache (if cache module is available)
            try:
                from app.cache import cache_manager
                from app.database import SessionLocal
                db = SessionLocal()
                cache_manager.clear_expired_cache(db)
                db.close()
            except ImportError:
                pass
            
            # Wait 1 hour before next cleanup
            await asyncio.sleep(3600)
            
        except Exception as e:
            print(f"Background cleanup error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error

# Global task manager instance
task_manager = TaskManager()

# API helper functions
def submit_async_task(task_name: str, task_func: Callable, *args, **kwargs) -> str:
    """Submit an async task and return task ID"""
    return task_manager.submit_task(task_name, task_func, *args, **kwargs)

def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Get status of a task"""
    task = task_manager.get_task(task_id)
    return task.to_dict() if task else None

def cancel_task(task_id: str) -> bool:
    """Cancel a running task"""
    return task_manager.cancel_task(task_id)

def get_all_tasks() -> List[Dict[str, Any]]:
    """Get all tasks"""
    return [task.to_dict() for task in task_manager.get_all_tasks()]

def cleanup_old_tasks(hours: int = 24):
    """Cleanup old tasks"""
    task_manager.cleanup_old_tasks(hours)

# Note: Background cleanup task should be started manually when needed
# Background task can be started with: asyncio.create_task(background_cleanup_task())
