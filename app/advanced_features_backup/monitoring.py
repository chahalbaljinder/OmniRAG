# app/monitoring.py - Advanced monitoring and logging

import time
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from functools import wraps
from sqlalchemy.orm import Session
import logging
import sys
import os

from app.database import get_db, SystemLog
from app.config import settings

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # File handler if log file is specified
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

logger = setup_logging()

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics = {}
        self.enabled = settings.enable_performance_logging
    
    def record_metric(self, metric_name: str, value: float, tags: Dict[str, Any] = None):
        """Record a performance metric"""
        if not self.enabled:
            return
        
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        metric_data = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "tags": tags or {}
        }
        
        self.metrics[metric_name].append(metric_data)
        
        # Keep only last 1000 entries per metric
        if len(self.metrics[metric_name]) > 1000:
            self.metrics[metric_name] = self.metrics[metric_name][-1000:]
    
    def get_metrics(self, metric_name: str = None) -> Dict[str, Any]:
        """Get performance metrics"""
        if metric_name:
            return self.metrics.get(metric_name, [])
        return self.metrics
    
    def get_statistics(self, metric_name: str) -> Dict[str, float]:
        """Get statistical summary of a metric"""
        if metric_name not in self.metrics:
            return {}
        
        values = [m["value"] for m in self.metrics[metric_name]]
        if not values:
            return {}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1] if values else 0
        }

# Global performance monitor
performance_monitor = PerformanceMonitor()

def log_to_database(level: str, message: str, component: str, user_id: Optional[int] = None, metadata: Dict[str, Any] = None):
    """Log message to database"""
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        
        log_entry = SystemLog(
            level=level,
            message=message,
            component=component,
            user_id=user_id,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        db.add(log_entry)
        db.commit()
        db.close()
        
    except Exception as e:
        logger.error(f"Failed to log to database: {e}")

def performance_timer(component: str = None, log_to_db: bool = True):
    """Decorator to measure function execution time"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            component_name = component or f"{func.__module__}.{func.__name__}"
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record performance metric
                performance_monitor.record_metric(
                    f"{component_name}.execution_time",
                    duration,
                    {"status": "success"}
                )
                
                if log_to_db:
                    log_to_database(
                        "INFO",
                        f"Function {func.__name__} executed successfully",
                        component_name,
                        metadata={"execution_time": duration}
                    )
                
                logger.info(f"{component_name} executed in {duration:.3f}s")
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error metric
                performance_monitor.record_metric(
                    f"{component_name}.execution_time",
                    duration,
                    {"status": "error", "error": str(e)}
                )
                
                if log_to_db:
                    log_to_database(
                        "ERROR",
                        f"Function {func.__name__} failed: {str(e)}",
                        component_name,
                        metadata={
                            "execution_time": duration,
                            "error": str(e),
                            "traceback": traceback.format_exc()
                        }
                    )
                
                logger.error(f"{component_name} failed after {duration:.3f}s: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            component_name = component or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record performance metric
                performance_monitor.record_metric(
                    f"{component_name}.execution_time",
                    duration,
                    {"status": "success"}
                )
                
                logger.info(f"{component_name} executed in {duration:.3f}s")
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error metric
                performance_monitor.record_metric(
                    f"{component_name}.execution_time",
                    duration,
                    {"status": "error", "error": str(e)}
                )
                
                logger.error(f"{component_name} failed after {duration:.3f}s: {e}")
                raise
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # Check if async
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class SystemMonitor:
    """System resource and health monitoring"""
    
    def __init__(self):
        self.start_time = time.time()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            import psutil
            
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process info
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_total": memory.total,
                    "memory_available": memory.available,
                    "memory_percent": memory.percent,
                    "disk_total": disk.total,
                    "disk_free": disk.free,
                    "disk_percent": disk.percent
                },
                "process": {
                    "pid": process.pid,
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads(),
                    "create_time": process.create_time()
                },
                "uptime": time.time() - self.start_time
            }
            
        except ImportError:
            # psutil not available, return basic info
            return {
                "system": {"error": "psutil not installed"},
                "process": {"pid": os.getpid()},
                "uptime": time.time() - self.start_time
            }
        except Exception as e:
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        try:
            # Database check
            from app.database import SessionLocal
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            health_status["checks"]["database"] = {"status": "ok"}
        except Exception as e:
            health_status["checks"]["database"] = {"status": "error", "error": str(e)}
            health_status["status"] = "unhealthy"
        
        # File system checks
        try:
            upload_dir = settings.upload_directory
            index_dir = settings.index_directory
            
            health_status["checks"]["filesystem"] = {
                "upload_dir_exists": os.path.exists(upload_dir),
                "upload_dir_writable": os.access(upload_dir, os.W_OK),
                "index_dir_exists": os.path.exists(index_dir),
                "index_dir_writable": os.access(index_dir, os.W_OK),
                "status": "ok"
            }
        except Exception as e:
            health_status["checks"]["filesystem"] = {"status": "error", "error": str(e)}
            health_status["status"] = "unhealthy"
        
        # Performance metrics
        try:
            health_status["checks"]["performance"] = {
                "metrics_count": len(performance_monitor.metrics),
                "status": "ok"
            }
        except Exception as e:
            health_status["checks"]["performance"] = {"status": "error", "error": str(e)}
        
        return health_status

# Global system monitor
system_monitor = SystemMonitor()

class ErrorTracker:
    """Track and analyze errors"""
    
    def __init__(self):
        self.errors = []
        self.max_errors = 1000
    
    def track_error(self, error: Exception, context: Dict[str, Any] = None):
        """Track an error with context"""
        error_data = {
            "type": type(error).__name__,
            "message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        self.errors.append(error_data)
        
        # Keep only last N errors
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
        
        # Log to database
        log_to_database(
            "ERROR",
            f"{error_data['type']}: {error_data['message']}",
            "ERROR_TRACKER",
            metadata=error_data
        )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics"""
        if not self.errors:
            return {"total_errors": 0}
        
        error_types = {}
        recent_errors = []
        
        for error in self.errors[-100:]:  # Last 100 errors
            error_type = error["type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            if len(recent_errors) < 10:
                recent_errors.append({
                    "type": error["type"],
                    "message": error["message"],
                    "timestamp": error["timestamp"]
                })
        
        return {
            "total_errors": len(self.errors),
            "error_types": error_types,
            "recent_errors": recent_errors
        }

# Global error tracker
error_tracker = ErrorTracker()

# Global monitoring instances
performance_monitor = PerformanceMonitor()
system_monitor = SystemMonitor()

# API helper functions for compatibility
def monitor_operation(operation_name: str, duration: float, metadata: Dict[str, Any] = None):
    """Monitor an operation"""
    performance_monitor.record_operation(operation_name, duration, metadata or {})

def get_monitoring_dashboard() -> Dict[str, Any]:
    """Get monitoring dashboard data"""
    return {
        "performance": performance_monitor.get_summary(),
        "system": system_monitor.get_system_health(),
        "errors": error_tracker.get_summary()
    }

def log_security_event(event_type: str, details: Dict[str, Any], user_id: Optional[int] = None):
    """Log a security event"""
    message = f"Security event: {event_type}"
    log_to_database("WARNING", message, "SECURITY", user_id, details)

def monitor_performance(operation: str, start_time: float, end_time: float, metadata: Dict[str, Any] = None):
    """Monitor performance of an operation"""
    duration = end_time - start_time
    monitor_operation(operation, duration, metadata)
