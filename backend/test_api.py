import requests
import json

url = "https://claverica-backend-production.up.railway.app/api/accounts/register/"
data = {
    "email": "test@example.com",
    "password": "Test123!@#",
    "confirm_password": "Test123!@#",
    "first_name": "Test",
    "last_name": "User",
    "phone": "+1234567890"
}

headers = {"Content-Type": "application/json"}

response = requests.post(url, json=data, headers=headers)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
