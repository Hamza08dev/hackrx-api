import requests

# Test health endpoint
print("Testing health endpoint...")
try:
    response = requests.get("https://hackrx-api-uc43.onrender.com/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50 + "\n")

# Test main endpoint
print("Testing main endpoint...")
url = "https://hackrx-api-uc43.onrender.com/hackrx/run"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test_key_123"
}
data = {
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "questions": [
        "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?"
    ]
}

try:
    response = requests.post(url, headers=headers, json=data, timeout=180)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}") 