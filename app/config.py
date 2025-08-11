# app/config.py - Configuration management

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # API Configuration
    app_name: str = "RAG Pipeline API"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # Database Configuration - Vercel compatible
    database_url: str = "sqlite:///tmp/rag_database.db"  # Use /tmp for Vercel
    
    # Authentication Configuration
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    secret_key: Optional[str] = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis Configuration - Disabled by default for Vercel
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False
    
    # File Upload Configuration - Vercel compatible
    max_upload_size: int = 50 * 1024 * 1024  # 50MB for Vercel limits
    max_files_per_request: int = 10  # Reduced for serverless
    max_pages_per_document: int = 500  # Reduced for serverless
    upload_directory: str = "/tmp/uploads"  # Use /tmp for Vercel
    index_directory: str = "/tmp/indexes"  # Use /tmp for Vercel
    
    # LLM Configuration
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    default_llm_provider: str = "gemini"
    
    # RAG Configuration - Optimized for serverless
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 600  # Smaller chunks for faster processing
    chunk_overlap: int = 100
    chunking_strategy: str = "word"  # word, sentence, paragraph
    similarity_threshold: float = 0.1
    max_search_results: int = 3  # Reduced for faster response
    max_chunk_size: int = 800  # Reduced for serverless
    overlap_size: int = 150  # Reduced for serverless
    
    # Rate Limiting
    rate_limit_uploads: str = "10/minute"
    rate_limit_queries: str = "30/minute"
    
    # Security
    allowed_file_types: list = [".pdf"]
    enable_file_scanning: bool = True
    sanitize_filenames: bool = True
    
    # Performance
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    enable_async_processing: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    enable_performance_logging: bool = True
    
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    
    model_config = ConfigDict(env_file=".env", env_prefix="RAG_")

# Global settings instance
settings = Settings()

def get_database_url() -> str:
    """Get database URL with absolute path for SQLite"""
    if settings.database_url.startswith("sqlite:///"):
        # Convert to absolute path
        db_path = settings.database_url.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, db_path)
        return f"sqlite:///{db_path}"
    return settings.database_url

def get_upload_directory() -> str:
    """Get absolute path for upload directory"""
    if not os.path.isabs(settings.upload_directory):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, settings.upload_directory)
    return settings.upload_directory

def get_index_directory() -> str:
    """Get absolute path for index directory"""
    if not os.path.isabs(settings.index_directory):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, settings.index_directory)
    return settings.index_directory

# Environment-specific configurations
class DevelopmentConfig(Settings):
    debug: bool = True
    log_level: str = "DEBUG"
    enable_performance_logging: bool = True

class ProductionConfig(Settings):
    debug: bool = False
    log_level: str = "WARNING"
    enable_caching: bool = True
    enable_async_processing: bool = True

class TestingConfig(Settings):
    database_url: str = "sqlite:///./test_rag_database.db"
    debug: bool = True
    log_level: str = "DEBUG"
    max_files_per_request: int = 5  # Lower for testing

def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("RAG_ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()
