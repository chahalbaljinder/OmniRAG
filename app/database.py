from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")  # user, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    documents = relationship("Document", back_populates="owner")
    queries = relationship("Query", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)  # Friendly name for the key
    key_hash = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    last_used = Column(DateTime)
    usage_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    file_size = Column(Integer)
    page_count = Column(Integer)
    chunk_count = Column(Integer)
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_hash = Column(String, index=True)
    file_metadata = Column(Text)  # JSON string for additional metadata
    owner_id = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=False)
    
    # Relationships
    owner = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    chunk_index = Column(Integer)
    content = Column(Text)
    embedding_vector = Column(Text)  # Serialized vector
    page_number = Column(Integer)
    word_count = Column(Integer)
    chunk_type = Column(String, default="text")  # text, table, image_caption
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
class Query(Base):
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text)
    response_text = Column(Text)
    processing_time = Column(Float)
    documents_used = Column(Text)  # JSON string of document IDs
    timestamp = Column(DateTime, default=datetime.utcnow)
    retrieval_score = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))
    search_type = Column(String, default="semantic")  # semantic, hybrid, keyword
    
    # Relationships
    user = relationship("User", back_populates="queries")

class QueryCache(Base):
    __tablename__ = "query_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    query_hash = Column(String, unique=True, index=True)
    query_text = Column(Text)
    response_text = Column(Text)
    documents_hash = Column(String)  # Hash of document IDs used
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    hit_count = Column(Integer, default=0)
    
class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String)  # INFO, WARNING, ERROR
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    component = Column(String)  # API, RAG, EMBEDDING, etc.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    log_metadata = Column(Text)  # JSON string for additional data

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    name = Column(String)
    state = Column(String, default="pending")  # pending, running, completed, failed, cancelled
    progress = Column(Float, default=0.0)
    result = Column(Text)  # JSON string
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    task_metadata = Column(Text)  # JSON string for additional data
    
    # Relationships
    user = relationship("User")

# Database setup
def get_database_url():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "rag_database.db")
    return f"sqlite:///{db_path}"

DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)

def init_db():
    """Initialize the database with tables"""
    print("🔄 Initializing database...")
    try:
        create_tables()
        print("✅ Database initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def drop_tables():
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)
