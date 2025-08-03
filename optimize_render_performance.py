#!/usr/bin/env python3
"""
Optimize for Render Performance
"""

import time
import requests
import tempfile
import os
import psutil
import gc

print("🚀 Testing Render Performance Optimizations")
print("=" * 40)

def test_memory_usage():
    """Test current memory usage."""
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"📊 Current memory usage: {memory_mb:.1f} MB")
    return memory_mb

def test_pdf_with_optimizations():
    """Test PDF processing with memory optimizations."""
    url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
    
    # Pre-test memory
    initial_memory = test_memory_usage()
    
    print("\n📥 Downloading PDF...")
    start_time = time.time()
    
    try:
        response = requests.get(url, timeout=30)
        download_time = time.time() - start_time
        file_size_mb = len(response.content) / 1024 / 1024
        
        print(f"✅ Download: {download_time:.2f}s ({file_size_mb:.1f} MB)")
        
        # Memory after download
        download_memory = test_memory_usage()
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(response.content)
            pdf_path = tmp_file.name
        
        # Clear response from memory
        del response
        gc.collect()
        
        print("\n📄 Extracting text...")
        start_time = time.time()
        
        from ingestion.document_loader import extract_text_from_pdf
        text = extract_text_from_pdf(pdf_path)
        
        extraction_time = time.time() - start_time
        print(f"✅ Extraction: {extraction_time:.2f}s ({len(text)} chars)")
        
        # Memory after extraction
        extraction_memory = test_memory_usage()
        
        # Cleanup
        os.unlink(pdf_path)
        del text
        gc.collect()
        
        # Final memory
        final_memory = test_memory_usage()
        
        print("\n📊 PERFORMANCE SUMMARY:")
        print(f"   Download time: {download_time:.2f}s")
        print(f"   Extraction time: {extraction_time:.2f}s")
        print(f"   Total time: {download_time + extraction_time:.2f}s")
        print(f"   File size: {file_size_mb:.1f} MB")
        print(f"   Memory delta: {final_memory - initial_memory:.1f} MB")
        
        # Recommendations
        if download_time > 5:
            print("⚠️ Download is slow - consider caching")
        if extraction_time > 10:
            print("⚠️ Extraction is slow - consider chunking")
        if final_memory - initial_memory > 100:
            print("⚠️ High memory usage - consider streaming")
            
        return download_time + extraction_time
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    test_pdf_with_optimizations()
    print("=" * 40) 