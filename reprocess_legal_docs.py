#!/usr/bin/env python3
"""
Script to reprocess specific legal documents with enhanced metadata
"""

import os
import sys

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def reprocess_legal_documents():
    """Reprocess legal documents with enhanced metadata"""
    try:
        from app.embedding import create_faiss_index, create_global_faiss_index
        
        # List of legal documents to reprocess
        legal_docs = [
            'uploads/legaldoc1.pdf',
            'uploads/legaldoc2.pdf'
        ]
        
        processed_count = 0
        for doc_path in legal_docs:
            if os.path.exists(doc_path):
                try:
                    print(f"Reprocessing {doc_path}...")
                    chunk_count = create_faiss_index(doc_path, document_id=None)
                    print(f"Successfully reprocessed {doc_path} with {chunk_count} chunks")
                    processed_count += 1
                except Exception as e:
                    print(f"Error reprocessing {doc_path}: {str(e)}")
            else:
                print(f"File not found: {doc_path}")
        
        if processed_count > 0:
            print(f"\nRebuilding global index...")
            global_chunks = create_global_faiss_index()
            print(f"Global index rebuilt with {global_chunks} total chunks")
        
        return processed_count
        
    except Exception as e:
        print(f"Error reprocessing documents: {str(e)}")
        return 0

if __name__ == "__main__":
    count = reprocess_legal_documents()
    print(f"\nReprocessed {count} legal documents")
