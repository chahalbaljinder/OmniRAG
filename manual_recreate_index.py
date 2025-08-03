#!/usr/bin/env python3
"""
Script to manually recreate the global FAISS index with enhanced metadata
"""

import os
import sys
import faiss
import pickle
import numpy as np

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def recreate_global_index_manual():
    """Manually recreate the global FAISS index"""
    try:
        # Define paths
        PROJECT_ROOT = project_root
        INDEX_DIR = os.path.join(PROJECT_ROOT, "indexes")
        faiss_index_dir = os.path.join(PROJECT_ROOT, "faiss_index")
        os.makedirs(faiss_index_dir, exist_ok=True)
        
        global_index_path = os.path.join(faiss_index_dir, "index.faiss")
        global_metadata_path = os.path.join(faiss_index_dir, "index.pkl")
        
        all_embeddings = []
        all_metadata = []
        EMBEDDING_DIM = 384
        
        print(f"Scanning directory: {INDEX_DIR}")
        
        # Scan all individual indexes
        for filename in os.listdir(INDEX_DIR):
            if filename.endswith(".index"):
                print(f"Processing: {filename}")
                index_file = os.path.join(INDEX_DIR, filename)
                meta_file = index_file + ".meta"
                
                if os.path.exists(meta_file):
                    try:
                        # Load individual index
                        index = faiss.read_index(index_file)
                        print(f"  Loaded index with {index.ntotal} vectors")
                        
                        # Load metadata
                        with open(meta_file, "rb") as f:
                            metadata = pickle.load(f)
                        print(f"  Loaded {len(metadata)} metadata items")
                        
                        # Clean metadata to ensure JSON serializable types
                        cleaned_metadata = []
                        for item in metadata:
                            if isinstance(item, dict):
                                cleaned_item = {
                                    "content": str(item.get("content", "")),
                                    "chunk_id": int(item.get("chunk_id", 0)),
                                    "document_id": int(item.get("document_id", 0)) if item.get("document_id") is not None else None,
                                    "source_file": str(item.get("source_file", filename.replace(".index", ""))),
                                    "chunk_index": int(item.get("chunk_index", 0)),
                                    "word_count": int(item.get("word_count", 0)),
                                    "char_count": int(item.get("char_count", 0)),
                                    "page_number": item.get("page_number", "N/A"),
                                    "start_char": item.get("start_char"),
                                    "end_char": item.get("end_char"),
                                    "section": item.get("section"),
                                }
                                
                                # Add comprehensive case metadata fields
                                case_fields = [
                                    'Case_Name', 'Case_No', 'Judges', 'Order_Date', 
                                    'Adjudication_Deadline', 'Appellant', 'Appellant_Advocate',
                                    'Respondents', 'Respondent_Advocates', 'Court', 'Filing_Date'
                                ]
                                
                                for field in case_fields:
                                    if field in item:
                                        cleaned_item[field] = item[field]
                                        print(f"    Found {field}: {item[field]}")
                                
                                cleaned_metadata.append(cleaned_item)
                            else:
                                # Handle legacy format - just strings
                                cleaned_metadata.append({
                                    "content": str(item),
                                    "chunk_id": len(cleaned_metadata),
                                    "document_id": None,
                                    "source_file": filename.replace(".index", ""),
                                    "chunk_index": len(cleaned_metadata),
                                    "word_count": len(str(item).split()),
                                    "char_count": len(str(item)),
                                    "page_number": "N/A"
                                })
                        
                        # Extract embeddings from the index
                        embeddings = index.reconstruct_n(0, index.ntotal)
                        
                        all_embeddings.append(embeddings)
                        all_metadata.extend(cleaned_metadata)
                        
                    except Exception as e:
                        print(f"Error processing {filename}: {str(e)}")
                        continue
        
        if all_embeddings:
            print(f"Combining {len(all_embeddings)} embedding sets...")
            # Combine all embeddings
            combined_embeddings = np.vstack(all_embeddings)
            print(f"Combined shape: {combined_embeddings.shape}")
            
            # Create global index
            global_index = faiss.IndexFlatIP(EMBEDDING_DIM)
            faiss.normalize_L2(combined_embeddings)
            global_index.add(combined_embeddings)
            
            # Save global index
            faiss.write_index(global_index, global_index_path)
            print(f"Saved global index to: {global_index_path}")
            
            # Save global metadata
            with open(global_metadata_path, "wb") as f:
                pickle.dump(all_metadata, f)
            print(f"Saved global metadata to: {global_metadata_path}")
            
            print(f"✅ Created global FAISS index with {len(all_metadata)} chunks from {len(all_embeddings)} documents")
            return len(all_metadata)
        else:
            print("❌ No individual indexes found to create global index")
            return 0
            
    except Exception as e:
        print(f"❌ Error creating global FAISS index: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    result = recreate_global_index_manual()
    print(f"\nFinal result: {result} chunks processed")
