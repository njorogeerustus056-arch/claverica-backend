import requests
import json

# Try these common passwords
passwords = [
    "AdminPassword123",  # Common superuser password
    "password123",
    "admin123",
    "Admin@123",
    "erustusnyaga001",  # Your username
    "Claverica2024",
    "Test@1234"
]

email = "erustusnyaga001@gmail.com"

for pwd in passwords:
    print(f"Trying: {pwd[:5]}...")
    r = requests.post(
        "https://claverica-backend-rniq.onrender.com/api/auth/login/",
        json={"email": email, "password": pwd},
        timeout=5
    )
    if r.status_code == 200:
        token = r.json()["access"]
        print(f"✅ SUCCESS! Password: {pwd}")
        print(f"Token: {token[:50]}...")
        break
    elif r.status_code != 401:
        print(f"Status {r.status_code}: {r.text[:50]}")
