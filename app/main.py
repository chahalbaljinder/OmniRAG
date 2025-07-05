from fastapi import FastAPI
from dotenv import load_dotenv
from app.api import router as api_router

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="RAG API",
    description="Upload documents and query them using LLMs with RAG.",
    version="1.0.0"
)

# Include API routes
app.include_router(api_router)
