#!/usr/bin/env python3
"""
Quick test for deployed HackRx API
"""

import requests
import json
import time

def test_api():
    """Test the deployed API."""
    
    print("🧪 Testing Deployed HackRx API")
    print("=" * 50)
    
    # API details
    url = "https://hackrx-api-uc43.onrender.com/hackrx/run"
    headers = {
        "Content-Type": "application/json"
    }
    
    # Test data
    data = {
        "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
        "questions": [
            "What is the grace period for premium payment?"
        ]
    }
    
    print(f"📡 Sending request to: {url}")
    print(f"📄 Document URL: {data['documents'][:50]}...")
    print(f"❓ Question: {data['questions'][0]}")
    print(f"⏱️ Timeout: 120 seconds")
    print()
    
    try:
        start_time = time.time()
        
        # Make the request
        response = requests.post(
            url, 
            headers=headers, 
            json=data, 
            timeout=120
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️ Response time: {processing_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"📝 Response: {json.dumps(result, indent=2)}")
            
            # Show answers
            answers = result.get("answers", [])
            print(f"\n🎯 Answers ({len(answers)}):")
            for i, answer in enumerate(answers, 1):
                print(f"   {i}. {answer}")
                
        else:
            print("❌ ERROR!")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 120 seconds")
        print("💡 This might be due to:")
        print("   - Cold start on free tier")
        print("   - Large document processing")
        print("   - API rate limits")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection error")
        print("💡 The API might be:")
        print("   - Starting up")
        print("   - Temporarily unavailable")
        print("   - Overloaded")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    test_api() 