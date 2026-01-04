import requests
import json

BASE_URL = "https://claverica-backend.onrender.com"

def test_my_credentials():
    print("🔐 Testing with YOUR Credentials")
    print("=" * 70)
    
    # Your credentials
    email = "eruznyaga001@gmail.com"
    password = "38876879Eruz"
    
    print(f"Email: {email}")
    print(f"Password: {password}")
    
    # 1. First try Login
    print("\n" + "=" * 40)
    print("1. Testing LOGIN")
    print("=" * 40)
    
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login/",
            json=login_data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'content-length']:
                print(f"  {key}: {value}")
        
        print(f"\nResponse Body:")
        if response.text:
            try:
                data = response.json()
                print(json.dumps(data, indent=2))
                
                # Check for tokens
                if response.status_code == 200:
                    access_token = data.get('access')
                    refresh_token = data.get('refresh')
                    
                    if access_token:
                        print(f"\n✅ Access Token obtained!")
                        print(f"Token (first 50 chars): {access_token[:50]}...")
                        
                        # Test /me endpoint
                        print("\n" + "=" * 40)
                        print("2. Testing /me endpoint with token")
                        print("=" * 40)
                        
                        # Try different token formats
                        token_formats = [
                            ("Bearer", f"Bearer {access_token}"),
                            ("Token", f"Token {access_token}"),
                            ("JWT", f"JWT {access_token}")
                        ]
                        
                        for token_type, auth_header in token_formats:
                            print(f"\nTrying {token_type} format...")
                            headers = {"Authorization": auth_header}
                            
                            me_response = requests.get(
                                f"{BASE_URL}/api/auth/me/",
                                headers=headers,
                                timeout=10
                            )
                            
                            print(f"  Status: {me_response.status_code}")
                            if me_response.status_code == 200:
                                print(f"  ✅ Success with {token_type}!")
                                try:
                                    user_data = me_response.json()
                                    print(f"  User data: {json.dumps(user_data, indent=4)}")
                                except:
                                    print(f"  Response: {me_response.text[:200]}")
                            else:
                                print(f"  Response: {me_response.text[:200]}")
                    
                    if refresh_token:
                        print(f"\nRefresh Token: {refresh_token[:50]}...")
                        
            except json.JSONDecodeError:
                print(f"Response (raw): {response.text}")
        else:
            print("(Empty response)")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # 2. If login failed, try registration
    print("\n" + "=" * 40)
    print("3. If login failed, trying REGISTRATION")
    print("=" * 40)
    
    try:
        if response.status_code != 200:
            registration_data = {
                "email": email,
                "password": password,
                "password2": password
            }
            
            reg_response = requests.post(
                f"{BASE_URL}/api/auth/register/",
                json=registration_data,
                timeout=10
            )
            
            print(f"Registration Status: {reg_response.status_code}")
            print(f"Registration Response: {reg_response.text}")
            
            if reg_response.status_code == 201:
                print("✅ Registration successful! Now try login again.")
    except Exception as e:
        print(f"Registration Error: {e}")
    
    # 3. Test other auth endpoints
    print("\n" + "=" * 40)
    print("4. Testing Other Authentication Endpoints")
    print("=" * 40)
    
    endpoints_to_test = [
        ("GET", "/api/auth/", "Index/Health check"),
        ("POST", "/api/auth/token/", "JWT Token (alternative login)"),
        ("POST", "/api/auth/logout/", "Logout"),
    ]
    
    for method, endpoint, description in endpoints_to_test:
        print(f"\n{description} ({endpoint}):")
        try:
            if method == "GET":
                resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            elif method == "POST":
                resp = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
            
            print(f"  Status: {resp.status_code}")
            if resp.text:
                print(f"  Response: {resp.text[:150]}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_my_credentials()