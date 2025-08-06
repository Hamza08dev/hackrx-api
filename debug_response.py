#!/usr/bin/env python3
"""
Debug Response - Check complete API response
"""

import requests
import json

print("🔍 Debugging API Response")
print("=" * 40)

url = "https://hackrx-api-uc43.onrender.com/hackrx/run"
headers = {
    "Content-Type": "application/json"
}

data = {
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "questions": ["What is the grace period for premium payment?"]
}

print("📡 Sending request...")

try:
    response = requests.post(url, headers=headers, json=data, timeout=120)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS!")
        print(f"\n📊 Response Keys: {list(result.keys())}")
        print(f"📝 Number of answers: {len(result.get('answers', []))}")
        
        print("\n🎯 FULL ANSWER:")
        print("-" * 40)
        full_answer = result['answers'][0]
        print(f"Answer length: {len(full_answer)} characters")
        print(f"Answer: {repr(full_answer)}")
        print("-" * 40)
        
        print("\n📄 PRETTY PRINTED:")
        print(json.dumps(result, indent=2))
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("=" * 40) 