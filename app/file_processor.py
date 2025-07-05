from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def process_file(file):
    reader = PdfReader(file.file)
    text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)
    from app.embedding import store_chunks
    store_chunks(chunks)
