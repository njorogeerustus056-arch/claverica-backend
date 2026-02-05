import requests
import json

# Test CORS headers
url = "http://localhost:8000/api/accounts/register/"
headers = {
    "Origin": "http://localhost:5173",
    "Content-Type": "application/json"
}
data = json.dumps({
    "email": "test@test.com",
    "password": "Test123!",
    "first_name": "Test",
    "last_name": "User"
})

try:
    # First test OPTIONS (preflight)
    resp = requests.options(url, headers=headers)
    print("OPTIONS Response:")
    print(f"  Status: {resp.status_code}")
    print(f"  Access-Control-Allow-Origin: {resp.headers.get('Access-Control-Allow-Origin', 'NOT FOUND')}")
    print(f"  Access-Control-Allow-Methods: {resp.headers.get('Access-Control-Allow-Methods', 'NOT FOUND')}")
    
    # Then test POST
    resp = requests.post(url, headers=headers, data=data)
    print("\nPOST Response:")
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {resp.text[:200]}")
    
except Exception as e:
    print(f"Error: {e}")
