# 🔍 RAG App – LLM Specialist Assignment

A Retrieval-Augmented Generation (RAG) pipeline that allows users to upload documents and ask contextual questions using FAISS vector search and a powerful LLM (LLaMA-3 via Groq API).

---

## 🚀 Features

- Upload **up to 20 PDFs**, max 1000 pages each
- Chunk documents & store embeddings in **FAISS**
- Query documents using **Groq's LLaMA 3 (70B)** LLM
- REST API built with **FastAPI**
- Dockerized for seamless local/cloud deployment
- Environment-configurable for multiple LLM providers

---

## 🧱 Tech Stack

- **FastAPI** – API framework  
- **FAISS** – Vector database  
- **SentenceTransformers** – Embedding generation  
- **Groq API** – High-performance LLMs  
- **Docker** – Deployment containerization

---

## ⚙️ Setup

### 1. Clone the repo & install dependencies

```bash
git clone <your-repo-url>
cd rag_app
```

### 2. Add `.env` file

Create a `.env` file:

```env
GROQ_API_KEY=gsk_live_your_api_key_here
```

### 3. Build and run via Docker

```bash
docker-compose up --build
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

## 🧪 Example CURL

```bash
curl -X POST http://localhost:8000/upload \
  -F "files=@unit1.pdf" \
  -F "files=@unit2.pdf"

curl -X POST http://localhost:8000/query \
  -d "query=What is unit 1 about?" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

---

## 🔄 Switching to OpenAI/Gemini

You can swap `rag.py` logic to use `openai.ChatCompletion.create()` or Google Gemini easily. Refer to respective SDKs and update the `.env`.

---

## 📂 Folder Structure

```
rag_app/
├── app/
│   ├── api.py
│   ├── rag.py
│   ├── embedding.py
│   ├── utils.py
│   ├── main.py
├── uploads/               ← stores uploaded PDFs
├── indexes/               ← stores FAISS indexes
├── .env                   ← your API key config
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## ✅ Status

✅ Fully working  
🧪 Test-ready via Swagger & Postman  
🚢 Deployable on cloud or local  

---

## 👤 Author

Anmol Airi – https://github.com/anmolairi03/pan-science-rag-pipeline/
