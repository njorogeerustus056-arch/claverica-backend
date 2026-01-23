import requests
import json

# Try with superuser you created
login_data = {"email": "erustusnyaga001@gmail.com", "password": "YOUR_SUPERUSER_PASSWORD"}

r = requests.post("https://claverica-backend-rniq.onrender.com/api/auth/login/", json=login_data)
print(f"Login status: {r.status_code}")

if r.status_code == 200:
    token = r.json()["access"]
    print(f"Token: {token[:30]}...")
    
    # Test /api/auth/me/ (THIS WORKS!)
    headers = {"Authorization": f"Bearer {token}"}
    r2 = requests.get("https://claverica-backend-rniq.onrender.com/api/auth/me/", headers=headers)
    print(f"/api/auth/me/ status: {r2.status_code}")
    print(f"Response: {r2.text[:200]}")
else:
    print("Login failed. Create new user:")
    reg_data = {"email": "test@test.com", "password": "Test123!", "first_name": "Test", "last_name": "User"}
    r3 = requests.post("https://claverica-backend-rniq.onrender.com/api/auth/register/", json=reg_data)
    print(f"Register status: {r3.status_code}")
    print(r3.text)
