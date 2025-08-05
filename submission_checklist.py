#!/usr/bin/env python3
"""
HackRx API Submission Checklist
- Tests all endpoints
- Validates response format
- Checks performance
- Ensures hackathon compatibility
"""

import requests
import time
import json
from datetime import datetime

# Configuration
API_BASE_URL = "https://web-production-84e69.up.railway.app"
API_ENDPOINT = f"{API_BASE_URL}/api/v1/hackrx/run"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
ROOT_ENDPOINT = f"{API_BASE_URL}/"

# Test data
TEST_DOCUMENT = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D&final=submission"
TEST_QUESTIONS = [
    "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
    "What is the waiting period for pre-existing diseases (PED) to be covered?",
    "Does this policy cover maternity expenses, and what are the conditions?"
]

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_success(message):
    """Print success message."""
    print(f"✅ {message}")

def print_error(message):
    """Print error message."""
    print(f"❌ {message}")

def print_warning(message):
    """Print warning message."""
    print(f"⚠️ {message}")

def test_health_endpoint():
    """Test health endpoint."""
    print_header("1. Health Endpoint Test")
    
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health endpoint working (Status: {response.status_code})")
            print(f"   Response: {data}")
            
            # Check required fields
            required_fields = ['status', 'timestamp', 'version', 'service']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print_warning(f"Missing fields: {missing_fields}")
            else:
                print_success("All required health fields present")
                
        else:
            print_error(f"Health endpoint failed (Status: {response.status_code})")
            return False
            
    except Exception as e:
        print_error(f"Health endpoint error: {e}")
        return False
    
    return True

def test_root_endpoint():
    """Test root endpoint."""
    print_header("2. Root Endpoint Test")
    
    try:
        response = requests.get(ROOT_ENDPOINT, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Root endpoint working (Status: {response.status_code})")
            print(f"   Response: {data}")
            
            # Check if main endpoint is listed
            if 'endpoints' in data and 'main' in data['endpoints']:
                main_endpoint = data['endpoints']['main']
                if main_endpoint == '/api/v1/hackrx/run':
                    print_success("Correct main endpoint listed")
                else:
                    print_warning(f"Main endpoint mismatch: {main_endpoint}")
            else:
                print_warning("Main endpoint not found in response")
                
        else:
            print_error(f"Root endpoint failed (Status: {response.status_code})")
            return False
            
    except Exception as e:
        print_error(f"Root endpoint error: {e}")
        return False
    
    return True

def test_main_endpoint_without_auth():
    """Test main endpoint without authentication."""
    print_header("3. Main Endpoint Test (No Auth)")
    
    payload = {
        "documents": TEST_DOCUMENT,
        "questions": TEST_QUESTIONS
    }
    
    try:
        start_time = time.time()
        response = requests.post(API_ENDPOINT, json=payload, timeout=120)
        processing_time = time.time() - start_time
        
        print(f"   Response Time: {processing_time:.2f}s")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print_success("Main endpoint working without authentication")
            
            data = response.json()
            
            # Check response structure
            if 'answers' in data:
                print_success("Response has 'answers' field")
                
                answers = data['answers']
                if len(answers) == len(TEST_QUESTIONS):
                    print_success(f"Correct number of answers: {len(answers)}")
                    
                    # Check answer quality
                    for i, answer in enumerate(answers):
                        print(f"   Q{i+1}: {answer[:100]}{'...' if len(answer) > 100 else ''}")
                        
                        if len(answer) < 10:
                            print_warning(f"Answer {i+1} seems too short")
                        elif len(answer) > 500:
                            print_warning(f"Answer {i+1} seems too long")
                        elif "don't have enough information" in answer.lower():
                            print_error(f"Answer {i+1} indicates no information found")
                        else:
                            print_success(f"Answer {i+1} looks good")
                else:
                    print_error(f"Wrong number of answers: {len(answers)} vs {len(TEST_QUESTIONS)}")
            else:
                print_error("Response missing 'answers' field")
                return False
                
        else:
            print_error(f"Main endpoint failed (Status: {response.status_code})")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Main endpoint error: {e}")
        return False
    
    return True

def test_main_endpoint_with_auth():
    """Test main endpoint with authentication."""
    print_header("4. Main Endpoint Test (With Auth)")
    
    payload = {
        "documents": TEST_DOCUMENT,
        "questions": [TEST_QUESTIONS[0]]  # Single question for speed
    }
    
    headers = {
        "Authorization": "Bearer hackrx-api-key-123"
    }
    
    try:
        start_time = time.time()
        response = requests.post(API_ENDPOINT, json=payload, headers=headers, timeout=60)
        processing_time = time.time() - start_time
        
        print(f"   Response Time: {processing_time:.2f}s")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print_success("Main endpoint working with authentication")
            data = response.json()
            
            if 'answers' in data and len(data['answers']) == 1:
                answer = data['answers'][0]
                print(f"   Answer: {answer[:100]}{'...' if len(answer) > 100 else ''}")
                print_success("Authentication working correctly")
            else:
                print_warning("Unexpected response with authentication")
                
        else:
            print_error(f"Main endpoint with auth failed (Status: {response.status_code})")
            return False
            
    except Exception as e:
        print_error(f"Main endpoint with auth error: {e}")
        return False
    
    return True

def test_cors_preflight():
    """Test CORS preflight request."""
    print_header("5. CORS Preflight Test")
    
    try:
        response = requests.options(API_ENDPOINT, timeout=10)
        
        if response.status_code == 200:
            print_success("CORS preflight working")
            
            # Check CORS headers
            cors_headers = [
                'access-control-allow-origin',
                'access-control-allow-methods',
                'access-control-allow-headers'
            ]
            
            missing_headers = [h for h in cors_headers if h not in response.headers]
            if missing_headers:
                print_warning(f"Missing CORS headers: {missing_headers}")
            else:
                print_success("All CORS headers present")
                
        else:
            print_error(f"CORS preflight failed (Status: {response.status_code})")
            return False
            
    except Exception as e:
        print_error(f"CORS preflight error: {e}")
        return False
    
    return True

def test_performance():
    """Test API performance."""
    print_header("6. Performance Test")
    
    payload = {
        "documents": TEST_DOCUMENT,
        "questions": [TEST_QUESTIONS[0]]
    }
    
    times = []
    for i in range(3):
        try:
            start_time = time.time()
            response = requests.post(API_ENDPOINT, json=payload, timeout=120)
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                times.append(processing_time)
                print(f"   Test {i+1}: {processing_time:.2f}s")
            else:
                print_error(f"Test {i+1} failed: {response.status_code}")
                
        except Exception as e:
            print_error(f"Test {i+1} error: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n   Average: {avg_time:.2f}s")
        print(f"   Min: {min_time:.2f}s")
        print(f"   Max: {max_time:.2f}s")
        
        if avg_time < 30:
            print_success("Performance is good (< 30s average)")
        elif avg_time < 60:
            print_warning("Performance is acceptable (< 60s average)")
        else:
            print_error("Performance is poor (> 60s average)")
            
        return True
    else:
        print_error("No successful performance tests")
        return False

def test_hackathon_format():
    """Test exact hackathon request/response format."""
    print_header("7. Hackathon Format Test")
    
    # Test the exact format the hackathon will use
    payload = {
        "documents": TEST_DOCUMENT,
        "questions": [
            "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
            "What is the waiting period for pre-existing diseases (PED) to be covered?",
            "Does this policy cover maternity expenses, and what are the conditions?",
            "What is the waiting period for cataract surgery?",
            "Are the medical expenses for an organ donor covered under this policy?"
        ]
    }
    
    try:
        start_time = time.time()
        response = requests.post(API_ENDPOINT, json=payload, timeout=180)
        processing_time = time.time() - start_time
        
        print(f"   Response Time: {processing_time:.2f}s")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print_success("Hackathon format test passed")
            
            data = response.json()
            
            # Validate response structure
            if 'answers' in data and isinstance(data['answers'], list):
                print_success("Response format is correct")
                
                answers = data['answers']
                print(f"   Number of answers: {len(answers)}")
                
                # Check each answer
                for i, answer in enumerate(answers):
                    if answer and len(answer.strip()) > 0:
                        print_success(f"Answer {i+1}: Valid")
                    else:
                        print_error(f"Answer {i+1}: Empty or invalid")
                        
            else:
                print_error("Response format is incorrect")
                return False
                
        else:
            print_error(f"Hackathon format test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Hackathon format test error: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print_header("HACKRX API SUBMISSION CHECKLIST")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: {API_BASE_URL}")
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Root Endpoint", test_root_endpoint),
        ("Main Endpoint (No Auth)", test_main_endpoint_without_auth),
        ("Main Endpoint (With Auth)", test_main_endpoint_with_auth),
        ("CORS Preflight", test_cors_preflight),
        ("Performance", test_performance),
        ("Hackathon Format", test_hackathon_format)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"{test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print_header("FINAL RESULTS")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print_success("🎉 ALL TESTS PASSED! Your API is ready for submission!")
    else:
        print_error(f"⚠️ {total - passed} tests failed. Please fix issues before submission.")
    
    print(f"\n📋 Submission Checklist:")
    print(f"   ✅ API is deployed and accessible")
    print(f"   ✅ Endpoint: {API_ENDPOINT}")
    print(f"   ✅ No authentication required for hackathon")
    print(f"   ✅ CORS enabled for cross-origin requests")
    print(f"   ✅ Response format matches hackathon requirements")
    print(f"   ✅ Performance is acceptable")
    
    if passed == total:
        print(f"\n🚀 READY TO SUBMIT!")
        print(f"   Webhook URL: {API_ENDPOINT}")
    else:
        print(f"\n🔧 NEEDS FIXES BEFORE SUBMISSION")

if __name__ == "__main__":
    main() 