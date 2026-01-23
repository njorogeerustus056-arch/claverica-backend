import requests
import json

# Login to get token
login_data = {
    "email": "erustusnyaga001@gmail.com",
    "password": "YOUR_SUPERUSER_PASSWORD"
}

try:
    r = requests.post(
        "https://claverica-backend-rniq.onrender.com/api/auth/login/",
        json=login_data,
        timeout=10
    )
    if r.status_code == 200:
        token = r.json().get('access')
        print(f"✅ Token: {token[:50]}...")
        
        # Test profile endpoint
        headers = {"Authorization": f"Bearer {token}"}
        r2 = requests.get(
            "https://claverica-backend-rniq.onrender.com/api/users/profile/",
            headers=headers,
            timeout=10
        )
        print(f"Profile status: {r2.status_code}")
        print(f"Response: {r2.text[:200]}")
    else:
        print(f"❌ Login failed: {r.status_code}")
        print(r.text)
except Exception as e:
    print(f"❌ Error: {e}")
