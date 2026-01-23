import requests
import json

# Register with confirm_password
reg_data = {
    "email": "testuser@claverica.com",
    "password": "Test123!",
    "confirm_password": "Test123!",
    "first_name": "Test",
    "last_name": "User"
}

r = requests.post(
    "https://claverica-backend-rniq.onrender.com/api/auth/register/",
    json=reg_data,
    timeout=10
)

print(f"Register status: {r.status_code}")
print(json.dumps(r.json(), indent=2))
