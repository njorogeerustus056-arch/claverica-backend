# test_endpoints.py
import requests
import json

# First get a token
login_url = "http://127.0.0.1:8000/api/auth/token/"
login_data = {"username": "admin", "password": "yourpassword"}

try:
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        token = response.json()["access"]
        print(f"Token: {token[:50]}...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test compliance
        urls_to_test = [
            "http://127.0.0.1:8000/api/compliance/api/dashboard/",
            "http://127.0.0.1:8000/api/compliance/dashboard/",
            "http://127.0.0.1:8000/api/compliance/api/user-status/",
            "http://127.0.0.1:8000/api/receipts/stats/",
            "http://127.0.0.1:8000/api/receipts/list/",
        ]
        
        for url in urls_to_test:
            try:
                resp = requests.get(url, headers=headers)
                print(f"\n{url}: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"  Success: {list(resp.json().keys())[:3]}...")
                elif resp.status_code != 404:
                    print(f"  Error: {resp.text[:100]}")
            except Exception as e:
                print(f"\n{url}: Error - {e}")
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")