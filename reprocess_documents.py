#!/usr/bin/env python3
"""
Script to reprocess existing documents with enhanced metadata extraction
"""

import os
import sys

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def reprocess_documents():
    """Reprocess existing documents to extract enhanced metadata"""
    try:
        from app.file_processor import DocumentProcessor
        from app.embedding import embedding_manager
        from app.utils import chunk_text
        
        uploads_dir = os.path.join(project_root, "uploads")
        indexes_dir = os.path.join(project_root, "indexes")
        
        if not os.path.exists(uploads_dir):
            print("No uploads directory found")
            return 0
        
        pdf_files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
        print(f"Found {len(pdf_files)} PDF files to reprocess")
        
        processed_count = 0
        
        for pdf_file in pdf_files:
            file_path = os.path.join(uploads_dir, pdf_file)
            print(f"\n🔄 Processing: {pdf_file}")
            
            try:
                # Extract text and enhanced metadata
                text, metadata = DocumentProcessor.extract_text_from_pdf(file_path)
                print(f"  Text length: {len(text)}")
                print(f"  Metadata keys: {list(metadata.keys())}")
                
                # Print extracted case metadata
                case_fields = [
                    'Case_Name', 'Case_No', 'Judges', 'Order_Date', 
                    'Adjudication_Deadline', 'Appellant', 'Appellant_Advocate',
                    'Respondents', 'Respondent_Advocates', 'Court', 'Filing_Date'
                ]
                
                found_case_data = False
                for field in case_fields:
                    if field in metadata:
                        print(f"  📋 {field}: {metadata[field]}")
                        found_case_data = True
                
                if not found_case_data:
                    print("  ⚠️  No case metadata extracted")
                
                # Create chunks with enhanced metadata
                chunks = chunk_text(text, strategy="word")
                
                # Add case metadata to each chunk
                enhanced_chunks = []
                for i, chunk in enumerate(chunks):
                    if isinstance(chunk, dict):
                        enhanced_chunk = chunk.copy()
                    else:
                        enhanced_chunk = {
                            "content": chunk,
                            "chunk_id": i,
                            "word_count": len(chunk.split())
                        }
                    
                    # Add all metadata to the chunk
                    enhanced_chunk.update(metadata)
                    enhanced_chunks.append(enhanced_chunk)
                
                print(f"  Created {len(enhanced_chunks)} enhanced chunks")
                
                # Create new FAISS index with enhanced metadata
                # Use a dummy document_id for reprocessing
                document_id = hash(pdf_file) % 10000  # Simple hash for demo
                chunk_count = embedding_manager.create_faiss_index_with_metadata(
                    file_path, document_id, enhanced_chunks
                )
                
                print(f"  ✅ Created index with {chunk_count} chunks")
                processed_count += 1
                
            except Exception as e:
                print(f"  ❌ Error processing {pdf_file}: {str(e)}")
                continue
        
        print(f"\n🎯 Reprocessed {processed_count} documents")
        return processed_count
        
    except Exception as e:
        print(f"❌ Error in reprocessing: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    result = reprocess_documents()
    print(f"\nFinal result: {result} documents reprocessed")
    
    if result > 0:
        print("\n🔄 Now recreating global index...")
        # Now recreate the global index
        exec(open('manual_recreate_index.py').read())
