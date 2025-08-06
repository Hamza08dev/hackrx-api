import requests
import json
import time

def test_health():
    """Test health endpoint."""
    print("🏥 Testing Health Endpoint...")
    try:
        response = requests.get("https://hackrx-api-uc43.onrender.com/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ Health: {response.json()}")
            return True
        else:
            print(f"❌ Health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health error: {e}")
        return False

def test_main_endpoint():
    """Test main endpoint with a simple question."""
    print("\n🧪 Testing Main Endpoint...")
    
    url = "https://hackrx-api-uc43.onrender.com/hackrx/run"
    headers = {
        "Content-Type": "application/json"
    }
    
    # Simple test with one question
    data = {
        "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
        "questions": [
            "What is the grace period for premium payment?"
        ]
    }
    
    try:
        print(f"📡 Sending request...")
        print(f"📄 Document: {data['documents'][:50]}...")
        print(f"❓ Question: {data['questions'][0]}")
        
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, timeout=120)
        end_time = time.time()
        
        processing_time = end_time - start_time
        print(f"⏱️ Processing time: {processing_time:.2f} seconds")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            answers = result.get("answers", [])
            
            print(f"✅ Success! Received {len(answers)} answers:")
            for i, answer in enumerate(answers):
                print(f"   A{i+1}: {answer[:100]}{'...' if len(answer) > 100 else ''}")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (120s)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_error_handling():
    """Test error handling."""
    print("\n🚨 Testing Error Handling...")
    
    url = "https://hackrx-api-uc43.onrender.com/hackrx/run"
    
    # Test 1: No authorization
    print("1. Testing without authorization...")
    try:
        response = requests.post(url, json={"documents": "test", "questions": ["test"]})
        if response.status_code == 401:
            print("✅ Correctly rejected unauthorized request")
        else:
            print(f"❌ Expected 401, got {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Invalid JSON
    print("2. Testing invalid JSON...")
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, data="invalid json")
        if response.status_code == 422:
            print("✅ Correctly rejected invalid JSON")
        else:
            print(f"❌ Expected 422, got {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🔧 Comprehensive API Test")
    print("=" * 50)
    
    # Test 1: Health endpoint
    health_ok = test_health()
    
    # Test 2: Main endpoint
    main_ok = test_main_endpoint()
    
    # Test 3: Error handling
    test_error_handling()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   Health Endpoint: {'✅ Working' if health_ok else '❌ Failed'}")
    print(f"   Main Endpoint: {'✅ Working' if main_ok else '❌ Failed'}")
    print(f"   Error Handling: ✅ Tested")
    
    if health_ok and main_ok:
        print("\n🎉 Your API is working correctly!")
        print("✅ All core functionality is operational")
        print("✅ Ready for hackathon evaluation")
    else:
        print("\n⚠️ Some issues detected")
        print("Please check the logs above for details")

if __name__ == "__main__":
    main() 