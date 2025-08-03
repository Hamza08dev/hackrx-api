#!/usr/bin/env python3
"""
Simple API test - shows complete results
"""

import requests
import time

print("🧪 Testing HackRx API")
print("=" * 40)

url = "https://hackrx-api-uc43.onrender.com/hackrx/run"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test_key_123"
}

data = {
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "questions": ["What is the grace period for premium payment?"]
}

print("📡 Sending request...")
start_time = time.time()

try:
    response = requests.post(url, headers=headers, json=data, timeout=120)
    end_time = time.time()
    
    print(f"⏱️ Time: {end_time - start_time:.1f}s")
    print(f"📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS!")
        print(f"🎯 Answer: {result['answers'][0]}")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("=" * 40) 