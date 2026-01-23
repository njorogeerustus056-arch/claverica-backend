import requests
import json

BASE_URL = "https://claverica-backend.onrender.com/api/accounts"

def test_with_csrf():
    print("Testing API with CSRF Protection")
    print("=" * 60)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Get CSRF token
    print("\n1. Getting CSRF token...")
    try:
        response = session.get(BASE_URL + "/")
        print(f"GET {BASE_URL}/ → {response.status_code}")
        print(f"Response: {response.text}")
        
        # Get CSRF token from cookies
        csrf_token = session.cookies.get('csrftoken')
        if csrf_token:
            print(f"✓ CSRF Token obtained: {csrf_token}")
        else:
            print("✗ No CSRF token found in cookies")
            print(f"Cookies: {session.cookies.get_dict()}")
            
    except Exception as e:
        print(f"Error: {e}")
        return
    
    # Step 2: Try registration with proper CSRF handling
    print("\n" + "=" * 60)
    print("2. Testing Registration...")
    print("=" * 60)
    
    import random
    test_id = random.randint(10000, 99999)
    test_email = f"testuser{test_id}@example.com"
    
    registration_data = [
        # Try simple registration first
        {"email": test_email, "password": "TestPass123!", "password2": "TestPass123!"},
        # Try with username
        {"username": f"user{test_id}", "email": test_email, "password": "TestPass123!", "password2": "TestPass123!"},
        # Try minimum required fields
        {"email": test_email, "password": "TestPass123!"}
    ]
    
    for i, data in enumerate(registration_data):
        print(f"\nAttempt {i+1}: {json.dumps(data)}")
        
        try:
            # Set up headers with CSRF token
            headers = {
                "Content-Type": "application/json",
                "Referer": "https://claverica-backend.onrender.com",
                "X-CSRFToken": csrf_token
            }
            
            response = session.post(
                BASE_URL + "/",
                json=data,
                headers=headers,
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response headers:")
            for key in ['Content-Type', 'Set-Cookie', 'Location']:
                if key in response.headers:
                    print(f"  {key}: {response.headers[key]}")
            
            print(f"Response body:")
            if response.text:
                try:
                    resp_json = response.json()
                    print(json.dumps(resp_json, indent=2))
                except:
                    print(response.text[:500])
            else:
                print("(Empty response)")
                
            # Check if we got new cookies
            new_csrf = session.cookies.get('csrftoken')
            if new_csrf and new_csrf != csrf_token:
                print(f"New CSRF token: {new_csrf}")
                csrf_token = new_csrf
                
        except Exception as e:
            print(f"Error: {e}")
    
    # Step 3: Try different content types
    print("\n" + "=" * 60)
    print("3. Testing Different Content Types...")
    print("=" * 60)
    
    test_data = {"email": "test@example.com", "password": "test123"}
    
    content_types = [
        ("application/json", lambda d: json.dumps(d)),
        ("application/x-www-form-urlencoded", lambda d: "&".join([f"{k}={v}" for k, v in d.items()])),
        ("multipart/form-data", lambda d: d)
    ]
    
    for content_type, serializer in content_types:
        print(f"\nTrying Content-Type: {content_type}")
        
        try:
            headers = {
                "Referer": "https://claverica-backend.onrender.com",
                "X-CSRFToken": csrf_token
            }
            
            if content_type == "application/json":
                headers["Content-Type"] = content_type
                data_to_send = serializer(test_data)
                response = session.post(BASE_URL + "/", data=data_to_send, headers=headers)
            elif content_type == "application/x-www-form-urlencoded":
                headers["Content-Type"] = content_type
                data_to_send = serializer(test_data)
                response = session.post(BASE_URL + "/", data=data_to_send, headers=headers)
            else:
                # multipart/form-data
                response = session.post(BASE_URL + "/", data=test_data, headers=headers)
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_with_csrf()