#!/usr/bin/env python3
"""
Debug PDF Processing Timing
"""

import time
import requests
import tempfile
import os
from ingestion.document_loader import extract_text_from_pdf

print("🔍 Debugging PDF Processing Timing")
print("=" * 40)

url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"

# Step 1: Download timing
print("📥 Step 1: Downloading PDF...")
start_time = time.time()
try:
    response = requests.get(url, timeout=30)
    download_time = time.time() - start_time
    print(f"✅ Download completed in {download_time:.2f}s")
    print(f"📊 File size: {len(response.content) / 1024 / 1024:.2f} MB")
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(response.content)
        pdf_path = tmp_file.name
    
    # Step 2: Text extraction timing
    print("\n📄 Step 2: Extracting text...")
    start_time = time.time()
    
    text = extract_text_from_pdf(pdf_path)
    
    extraction_time = time.time() - start_time
    print(f"✅ Text extraction completed in {extraction_time:.2f}s")
    print(f"📊 Text length: {len(text)} characters")
    print(f"📊 Text preview: {text[:200]}...")
    
    # Cleanup
    os.unlink(pdf_path)
    
    # Summary
    print("\n📊 TIMING SUMMARY:")
    print(f"   Download: {download_time:.2f}s")
    print(f"   Extraction: {extraction_time:.2f}s")
    print(f"   Total: {download_time + extraction_time:.2f}s")
    
    if extraction_time > 30:
        print("⚠️ Text extraction is slow (>30s)")
    elif download_time > 10:
        print("⚠️ Download is slow (>10s)")
    else:
        print("✅ Timing looks reasonable")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("=" * 40) 