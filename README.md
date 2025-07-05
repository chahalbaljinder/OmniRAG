# 🔍 RAG Pipeline API - Enhanced Edition

A comprehensive Retrieval-Augmented Generation (RAG) pipeline with advanced features including authentication, hybrid search, caching, monitoring, and async processing. Built with FastAPI and powered by Google's Gemini 2.0 Flash LLM.

---

## 🚀 Features

### Core Features
- **Multi-document Upload**: Support for up to 20 PDFs, max 1000 pages each
- **Advanced Search**: Hybrid search combining semantic and keyword matching
- **Multiple LLM Support**: Google Gemini 2.0 Flash (configurable for other providers)
- **Vector Database**: FAISS for efficient similarity search
- **Persistent Storage**: SQLite database for metadata and caching

### Advanced Features
- **🔐 Authentication & Authorization**: JWT tokens, API keys, role-based access
- **⚡ Async Processing**: Background processing for large files and complex queries
- **🧠 Intelligent Caching**: Query caching with automatic invalidation
- **📊 Monitoring & Analytics**: Performance metrics, system health, error tracking
- **🔍 Hybrid Search**: Combines semantic and keyword search with re-ranking
- **🛡️ Security**: Rate limiting, input validation, file scanning
- **📈 Performance Optimization**: In-memory caching, query optimization

---

## 🧱 Tech Stack

### Core Components
- **FastAPI** – High-performance API framework
- **FAISS** – Vector similarity search
- **SentenceTransformers** – Text embeddings
- **Google Gemini 2.0 Flash** – Advanced LLM
- **SQLAlchemy** – Database ORM
- **SQLite** – Persistent storage

### Enhanced Components
- **JWT + bcrypt** – Authentication & authorization
- **scikit-learn** – Advanced search algorithms
- **psutil** – System monitoring
- **asyncio** – Async task processing

---

## ⚙️ Setup & Installation

### 1. Clone & Install Dependencies

```bash
git clone <your-repo-url>
cd pan-science-rag-pipeline
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file with the following variables:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional - Advanced Configuration
RAG_JWT_SECRET_KEY=your_jwt_secret_key_here
RAG_DATABASE_URL=sqlite:///./rag_database.db
RAG_DEBUG=false
RAG_LOG_LEVEL=INFO
RAG_ENABLE_CACHING=true
RAG_ENABLE_ASYNC_PROCESSING=true
RAG_MAX_UPLOAD_SIZE=104857600
RAG_RATE_LIMIT_UPLOADS=10/minute
RAG_RATE_LIMIT_QUERIES=30/minute
```

### 3. Initialize Database

```bash
python -c "from app.database import create_tables; create_tables()"
```

### 4. Run the Application

```bash
# Development
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

> 🌐 **API Documentation**: `http://localhost:8000/docs`  
> 📊 **Health Check**: `http://localhost:8000/api/v2/health`

---

## 🔑 API Usage

### Authentication

#### Register User
```bash
curl -X POST http://localhost:8000/api/v2/auth/register \
  -F "username=myuser" \
  -F "email=user@example.com" \
  -F "password=securepassword"
```

#### Login & Get Token
```bash
curl -X POST http://localhost:8000/api/v2/auth/login \
  -F "username=myuser" \
  -F "password=securepassword"
```

#### Create API Key
```bash
curl -X POST http://localhost:8000/api/v2/auth/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "name=My API Key" \
  -F "expires_days=30"
```

### Document Management

#### Upload Documents (Sync)
```bash
curl -X POST http://localhost:8000/api/v2/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf" \
  -F "async_processing=false"
```

#### Upload Documents (Async)
```bash
curl -X POST http://localhost:8000/api/v2/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "files=@large_document.pdf" \
  -F "async_processing=true"
```

#### Check Upload Status
```bash
curl -X GET http://localhost:8000/api/v2/upload/status/TASK_ID \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Advanced Querying

#### Hybrid Search Query
```bash
curl -X POST http://localhost:8000/api/v2/query \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "query=What are the main machine learning algorithms discussed?" \
  -F "k=5" \
  -F "search_type=hybrid" \
  -F "use_cache=true" \
  -F "expand_query=true"
```

#### API Key Authentication
```bash
curl -X POST http://localhost:8000/api/v2/query \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "query=Summarize the research methodology" \
  -F "search_type=semantic"
```

#### Async Complex Query
```bash
curl -X POST http://localhost:8000/api/v2/query \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "query=Comprehensive analysis of all research papers" \
  -F "async_processing=true" \
  -F "search_type=hybrid"
```

### Document Management

#### List Documents
```bash
curl -X GET "http://localhost:8000/api/v2/documents?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Delete Document
```bash
curl -X DELETE http://localhost:8000/api/v2/documents/DOCUMENT_ID \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Monitoring & Analytics

#### System Health
```bash
curl -X GET http://localhost:8000/api/v2/health
```

#### System Statistics
```bash
curl -X GET http://localhost:8000/api/v2/stats \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Performance Metrics (Admin)
```bash
curl -X GET http://localhost:8000/api/v2/performance-metrics \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

---

## 📂 Project Structure

```
pan-science-rag-pipeline/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration management
│   ├── database.py             # Database models & session
│   ├── auth.py                 # Authentication & authorization
│   ├── api.py                  # Basic API endpoints (v1)
│   ├── api_enhanced.py         # Enhanced API endpoints (v2)
│   ├── rag.py                  # RAG logic with Gemini
│   ├── embedding.py            # FAISS indexing & embeddings
│   ├── search.py               # Hybrid search implementation
│   ├── cache.py                # Caching system
│   ├── monitoring.py           # Performance monitoring
│   ├── async_processing.py     # Async task management
│   ├── security.py             # Security & validation
│   ├── file_processor.py       # PDF processing
│   └── utils.py                # Utility functions
├── tests/
│   ├── test_api.py             # Basic API tests
│   └── test_enhanced_api.py    # Enhanced API tests
├── uploads/                    # Uploaded documents
├── indexes/                    # FAISS indexes
├── .env                        # Environment variables
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
├── postman_collection.json     # Postman API collection
└── README.md                   # This file
```

---

## 🔄 API Versions

### Basic API (v1) - `/api/v1/`
- Simple upload and query endpoints
- No authentication required
- Basic functionality for quick testing

### Enhanced API (v2) - `/api/v2/`
- Full authentication system
- Advanced search capabilities
- Async processing
- Monitoring and analytics
- Production-ready features

---

## 🚀 Advanced Features

### Hybrid Search
- **Semantic Search**: Vector similarity using embeddings
- **Keyword Search**: BM25 algorithm for exact matches
- **Combined Scoring**: Weighted combination of both approaches
- **Re-ranking**: Diversity and relevance optimization

### Caching System
- **Query Caching**: Automatic caching of query responses
- **In-Memory Cache**: Fast access for frequently used data
- **Cache Invalidation**: Smart invalidation on document changes
- **Performance Metrics**: Cache hit rates and statistics

### Async Processing
- **Background Tasks**: Long-running operations in background
- **Task Monitoring**: Track progress and status
- **Queue Management**: Automatic task scheduling
- **Error Handling**: Robust error recovery

### Monitoring & Analytics
- **Performance Metrics**: Response times, throughput
- **System Health**: CPU, memory, disk usage
- **Error Tracking**: Centralized error logging
- **User Analytics**: Usage patterns and statistics

### Security Features
- **JWT Authentication**: Secure token-based auth
- **API Key Support**: Alternative authentication method
- **Rate Limiting**: Prevent abuse and overuse
- **Input Validation**: Secure file and query validation
- **Role-Based Access**: Admin and user permissions

---

## 🧪 Testing

### Run Basic Tests
```bash
pytest tests/test_api.py -v
```

### Run Enhanced Tests
```bash
pytest tests/test_enhanced_api.py -v
```

### Run All Tests
```bash
pytest -v --tb=short
```

### Use Postman Collection
1. Import `postman_collection.json` into Postman
2. Set environment variables:
   - `base_url`: `http://localhost:8000`
   - `auth_token`: (obtained from login)
   - `api_key`: (obtained from API key creation)

---

## 📊 Performance & Scalability

### Optimization Features
- **Vector Database**: FAISS for fast similarity search
- **Embedding Caching**: Reduce computation overhead
- **Database Indexing**: Optimized query performance
- **Async Processing**: Non-blocking operations
- **Connection Pooling**: Efficient database connections

### Scalability Considerations
- **Horizontal Scaling**: Multiple worker processes
- **Load Balancing**: Distribute requests across workers
- **Database Scaling**: Supports migration to PostgreSQL
- **Caching Layers**: Redis integration ready
- **Microservices**: Modular architecture for splitting

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RAG_GEMINI_API_KEY` | - | **Required**: Google Gemini API key |
| `RAG_JWT_SECRET_KEY` | auto-generated | JWT signing secret |
| `RAG_DATABASE_URL` | `sqlite:///./rag_database.db` | Database connection string |
| `RAG_DEBUG` | `false` | Enable debug mode |
| `RAG_LOG_LEVEL` | `INFO` | Logging level |
| `RAG_ENABLE_CACHING` | `true` | Enable query caching |
| `RAG_CACHE_TTL` | `3600` | Cache TTL in seconds |
| `RAG_MAX_UPLOAD_SIZE` | `104857600` | Max file size (100MB) |
| `RAG_MAX_FILES_PER_REQUEST` | `20` | Max files per upload |
| `RAG_RATE_LIMIT_UPLOADS` | `10/minute` | Upload rate limit |
| `RAG_RATE_LIMIT_QUERIES` | `30/minute` | Query rate limit |

### Advanced Configuration
```python
# app/config.py
class Settings(BaseSettings):
    # Customize embedding model
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Adjust chunk parameters
    chunk_size: int = 800
    chunk_overlap: int = 100
    
    # Search configuration
    similarity_threshold: float = 0.1
    max_search_results: int = 5
```

---

## 🚀 Production Deployment

### Environment Setup
1. Set production environment variables
2. Configure proper database (PostgreSQL recommended)
3. Set up reverse proxy (Nginx)
4. Configure SSL certificates
5. Set up monitoring and logging

### Recommended Production Stack
- **Web Server**: Nginx (reverse proxy)
- **ASGI Server**: Uvicorn with Gunicorn
- **Database**: PostgreSQL
- **Cache**: Redis
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack

### Security Checklist
- [ ] Use strong JWT secret keys
- [ ] Configure proper CORS settings
- [ ] Set up rate limiting
- [ ] Enable HTTPS
- [ ] Validate all inputs
- [ ] Set up backup procedures
- [ ] Monitor security logs

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Install missing dependencies
pip install -r requirements.txt

# Check Python version (3.8+ required)
python --version
```

#### 2. Database Issues
```bash
# Recreate database
python -c "from app.database import drop_tables, create_tables; drop_tables(); create_tables()"
```

#### 3. API Key Issues
- Verify Gemini API key in `.env` file
- Check API key permissions and quota
- Ensure proper environment variable naming

#### 4. Memory Issues
- Reduce chunk size in configuration
- Enable async processing for large files
- Monitor system resources with `/api/v2/stats`

### Debug Mode
```bash
# Enable debug logging
export RAG_DEBUG=true
export RAG_LOG_LEVEL=DEBUG

# Run with debug info
python -m uvicorn app.main:app --reload --log-level debug
```

---

## 📈 Monitoring & Maintenance

### Health Monitoring
- **Health Endpoint**: `/api/v2/health`
- **System Stats**: `/api/v2/stats`
- **Performance Metrics**: `/api/v2/performance-metrics` (admin)

### Regular Maintenance
1. **Database Cleanup**: Remove old cache entries
2. **Log Rotation**: Archive old system logs
3. **Index Optimization**: Rebuild FAISS indexes
4. **Security Updates**: Update dependencies
5. **Backup Procedures**: Regular data backups

### Performance Tuning
1. Monitor query response times
2. Optimize chunk size and overlap
3. Adjust caching parameters
4. Review rate limiting settings
5. Scale worker processes as needed

---

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Install development dependencies
4. Run tests before submitting
5. Follow code style guidelines

### Code Style
- Use Black for Python formatting
- Follow PEP 8 guidelines
- Add type hints where possible
- Include docstrings for functions
- Write comprehensive tests

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini 2.0 Flash** - Advanced LLM capabilities
- **FAISS** - Efficient vector similarity search
- **FastAPI** - High-performance web framework
- **SentenceTransformers** - State-of-the-art embeddings

---

## 📞 Support

For support and questions:
- 📖 **Documentation**: Available at `/docs` endpoint
- 🐛 **Issues**: Create GitHub issues for bugs
- 💡 **Features**: Submit feature requests
- 📧 **Contact**: Reach out for enterprise support

---

**🚀 Built with ❤️ for the future of document intelligence**
