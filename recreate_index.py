#!/usr/bin/env python3
"""
Script to recreate the global FAISS index
"""

import os
import sys
import subprocess

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def recreate_global_index():
    """Recreate the global FAISS index"""
    try:
        from app.embedding import create_global_faiss_index
        result = create_global_faiss_index()
        print(f"Successfully recreated global index with {result} chunks")
        return result
    except Exception as e:
        print(f"Error recreating global index: {str(e)}")
        return 0

if __name__ == "__main__":
    recreate_global_index()
