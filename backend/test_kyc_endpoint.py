import requests
import json

# Test data for checking KYC requirement
test_data = {
    "service_type": "transfer",
    "amount": 2000  # Above $1500 threshold
}

print("Testing KYC requirement check...")
print(f"Test Data: {json.dumps(test_data, indent=2)}")
print("\nNote: You need to test this endpoint with authentication.")
print("Endpoint: POST http://localhost:8000/kyc/check-requirement/")
print("Headers: Content-Type: application/json")
print("Body: ", json.dumps(test_data, indent=2))
print("\nFor now, you can test via:")
print("1. Postman with authentication")
print("2. Browser console with fetch API")
print("3. Django test shell")
