# 🔍 RAG App – Gemini 2.0 Flash Edition

A Retrieval-Augmented Generation (RAG) pipeline that allows users to upload documents and ask contextual questions using FAISS vector search and Google's powerful Gemini 2.0 Flash LLM.

---

## 🚀 Features

- Upload **up to 20 PDFs**, max 1000 pages each
- Chunk documents & store embeddings in **FAISS**
- Query documents using **Google Gemini 2.0 Flash** LLM
- REST API built with **FastAPI**
- Environment-configurable for multiple LLM providers
- Proper file path handling for cross-platform compatibility

---

## 🧱 Tech Stack

- **FastAPI** – API framework  
- **FAISS** – Vector database  
- **SentenceTransformers** – Embedding generation  
- **Google Gemini 2.0 Flash** – Advanced LLM for responses
- **Python-dotenv** – Environment management

---

## ⚙️ Setup

### 1. Clone the repo & install dependencies

```bash
git clone <your-repo-url>
cd pan-science-rag-pipeline
pip install -r requirements.txt
```

### 2. Add `.env` file

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run the application

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

> App will be available at `http://localhost:8000/docs`

---

## 🧪 API Usage

### `POST /upload`
Upload up to 20 PDF files

- `files`: `multipart/form-data`

### `POST /query`
Ask a question based on all uploaded PDFs

- `query`: form field

### `GET /documents`
View metadata of all uploaded documents

---

## 🧪 Example Usage

```bash
# Upload documents
curl -X POST http://localhost:8000/upload \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf"

# Ask questions
curl -X POST http://localhost:8000/query \
  -d "query=What are the main topics discussed?" \
  -H "Content-Type: application/x-www-form-urlencoded"

# List documents
curl -X GET http://localhost:8000/documents
```

---

## 🔄 Key Features

- **Multi-document RAG**: Upload multiple PDFs and query across all of them
- **Gemini 2.0 Flash**: Latest Google LLM for high-quality responses
- **Vector Search**: FAISS-powered semantic search for relevant context
- **FastAPI**: Modern, fast web framework with automatic API documentation
- **Cross-platform**: Works on Windows, macOS, and Linux

---

## 📂 Project Structure

```
pan-science-rag-pipeline/
├── app/
│   ├── api.py              # FastAPI routes
│   ├── rag.py              # RAG logic with Gemini
│   ├── embedding.py        # FAISS indexing
│   ├── utils.py            # Utility functions
│   ├── file_processor.py   # PDF processing
│   └── main.py             # FastAPI app
├── tests/
│   └── test_api.py         # API tests
├── uploads/                # Uploaded PDFs (created automatically)
├── indexes/                # FAISS indexes (created automatically)
├── .env                    # Environment variables
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
└── README.md
```

---

## ✅ Status

✅ Fully working with Gemini 2.0 Flash  
🧪 Test-ready via Swagger & pytest  
🚢 Production-ready FastAPI application  

---

## 👤 Author

Enhanced RAG Pipeline with Gemini 2.0 Flash integration
