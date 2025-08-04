#!/usr/bin/env python3
"""
Performance Test for HackRx API
- Measures response times
- Tests with real document and questions
- Provides detailed timing breakdown
"""

import requests
import time
import json
from datetime import datetime

# API Configuration
API_URL = "https://web-production-84e69.up.railway.app/api/v1/hackrx/run"
API_KEY = "hackrx-api-key-123"  # Replace with your actual API key

# Test data
TEST_DOCUMENT = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"

TEST_QUESTIONS = [
    "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
    "What is the waiting period for pre-existing diseases (PED) to be covered?",
    "Does this policy cover maternity expenses, and what are the conditions?"
]

def test_api_performance():
    """Test API performance with timing measurements."""
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "documents": TEST_DOCUMENT,
        "questions": TEST_QUESTIONS
    }
    
    print("🚀 Starting Performance Test")
    print("=" * 50)
    print(f"📄 Document: {TEST_DOCUMENT[:50]}...")
    print(f"❓ Questions: {len(TEST_QUESTIONS)}")
    print(f"⏰ Start Time: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 50)
    
    # Start timing
    start_time = time.time()
    
    try:
        # Make API request
        print("📡 Making API request...")
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=300  # 5 minutes timeout
        )
        
        # Calculate timing
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✅ Response received in {total_time:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            answers = result.get('answers', [])
            
            print(f"📝 Generated {len(answers)} answers")
            print("-" * 50)
            
            # Display answers with timing
            for i, (question, answer) in enumerate(zip(TEST_QUESTIONS, answers)):
                print(f"Q{i+1}: {question[:60]}...")
                print(f"A{i+1}: {answer}")
                print()
            
            # Performance summary
            print("=" * 50)
            print("📈 PERFORMANCE SUMMARY")
            print("=" * 50)
            print(f"⏱️  Total Time: {total_time:.2f} seconds")
            print(f"📊 Average per question: {total_time/len(TEST_QUESTIONS):.2f} seconds")
            print(f"🚀 Questions per minute: {60/(total_time/len(TEST_QUESTIONS)):.1f}")
            
            # Performance rating
            if total_time < 30:
                rating = "🟢 EXCELLENT"
            elif total_time < 60:
                rating = "🟡 GOOD"
            elif total_time < 120:
                rating = "🟠 ACCEPTABLE"
            else:
                rating = "🔴 SLOW"
            
            print(f"🏆 Performance Rating: {rating}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (5 minutes)")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_single_question():
    """Test with a single question for quick timing."""
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "documents": TEST_DOCUMENT,
        "questions": [TEST_QUESTIONS[0]]  # Just the first question
    }
    
    print("🧪 Single Question Test")
    print("=" * 30)
    print(f"❓ Question: {TEST_QUESTIONS[0][:50]}...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=300
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"⏱️  Response Time: {total_time:.2f} seconds")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('answers', [])[0]
            print(f"📝 Answer: {answer}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Choose test type:")
    print("1. Full test (3 questions)")
    print("2. Quick test (1 question)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "2":
        test_single_question()
    else:
        test_api_performance() 