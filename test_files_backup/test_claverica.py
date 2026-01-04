# test_claverica.py
import requests
import json

print("=== Testing Claverica API with your credentials ===")
print("Email: eruznyaga001@gmail.com")
print("Password: 38876879Eruz")

# 1. Get JWT token
print("\n1. Getting JWT token...")
login_url = "http://127.0.0.1:8000/api/auth/token/"
login_data = {
    "username": "eruznyaga001@gmail.com",  # Using email as username
    "password": "38876879Eruz"
}

try:
    response = requests.post(login_url, json=login_data, timeout=10)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access"]
        print(f"   ✅ Token acquired!")
        print(f"   Token (first 50 chars): {access_token[:50]}...")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Test key endpoints
        print("\n2. Testing API endpoints...")
        
        endpoints = [
            ("Health check", "/health/", False),
            ("API root", "/", False),
            ("User profile", "/api/users/profile/", True),
            ("User settings", "/api/users/settings/", True),
            ("Tasks", "/api/tasks/", True),
            ("Transactions", "/api/transactions/", True),
            ("Cards", "/api/cards/", True),
            ("Receipts stats", "/api/receipts/stats/", True),
            ("Compliance dashboard", "/api/compliance/api/dashboard/", True),
        ]
        
        for name, endpoint, needs_auth in endpoints:
            url = f"http://127.0.0.1:8000{endpoint}"
            try:
                if needs_auth:
                    resp = requests.get(url, headers=headers, timeout=5)
                else:
                    resp = requests.get(url, timeout=5)
                
                if resp.status_code == 200:
                    print(f"   ✅ {name}: 200 OK")
                    # Show some data for user profile
                    if "profile" in endpoint and resp.status_code == 200:
                        data = resp.json()
                        print(f"      👤 User: {data.get('first_name', '')} {data.get('last_name', '')}")
                        print(f"      📧 Email: {data.get('email', '')}")
                        print(f"      💰 Balance: ${data.get('balance', 0):.2f}")
                elif resp.status_code == 404:
                    print(f"   ⚠️  {name}: 404 Not Found (check URL)")
                elif resp.status_code == 401:
                    print(f"   🔐 {name}: 401 Unauthorized (auth issue)")
                else:
                    print(f"   ❌ {name}: {resp.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"   ⏱️  {name}: Timeout")
            except Exception as e:
                print(f"   ❌ {name}: Error - {str(e)[:50]}")
        
        # 3. Show token info
        print("\n3. Token information:")
        # Decode token to see expiry (simplified)
        import base64
        try:
            parts = access_token.split('.')
            if len(parts) >= 2:
                payload = parts[1]
                # Add padding if needed
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.urlsafe_b64decode(payload)
                token_info = json.loads(decoded)
                print(f"   User ID: {token_info.get('user_id', 'N/A')}")
                print(f"   Token type: {token_info.get('token_type', 'N/A')}")
                print(f"   Expires at timestamp: {token_info.get('exp', 'N/A')}")
        except:
            print("   Could not decode token")
            
    else:
        print(f"   ❌ Failed to get token")
        print(f"   Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("   ❌ Cannot connect to server. Is it running?")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n=== Test Complete ===")