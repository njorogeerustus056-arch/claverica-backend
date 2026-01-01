import requests
import json

# Your credentials and token
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY3MTk1Nzg1LCJpYXQiOjE3NjcxOTIxODUsImp0aSI6ImQ0NWY4MjYxZDNhNjQzODg4Yzg2MDJhMTNiN2Q0NzA4IiwidXNlcl9pZCI6IjE3In0.UmgcvKeROIpQNtkwo0pm6lgRCQ-l0-lRNP6uCb66QVc"
base_url = "http://localhost:8000"

headers = {
    "Authorization": f"Bearer {access_token}"
}

def print_response(endpoint, response):
    print(f"\n{'='*60}")
    print(f"Testing: {endpoint}")
    print(f"Status: {response.status_code}")
    print('-'*60)
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print('='*60)

print("Testing Receipts API with your credentials...")

# 1. Test receipts list
response = requests.get(f"{base_url}/api/receipts/list/", headers=headers)
print_response("/api/receipts/list/", response)

# 2. Test receipts stats
response = requests.get(f"{base_url}/api/receipts/stats/", headers=headers)
print_response("/api/receipts/stats/", response)

# 3. Test user profile
response = requests.get(f"{base_url}/api/user/profile/", headers=headers)
print_response("/api/user/profile/", response)

# 4. Try to upload a test receipt
print("\nCreating a test receipt file...")
with open("test_receipt.txt", "w") as f:
    f.write("Test receipt content\nAmount: $29.99\nDate: 2024-01-16")

try:
    files = {
        'file': ('test_receipt.txt', open('test_receipt.txt', 'rb'), 'text/plain')
    }
    data = {
        'merchant_name': 'Test Store',
        'amount': '29.99',
        'currency': 'USD',
        'category': 'shopping',
        'notes': 'Test receipt upload'
    }
    
    print("\n" + "="*60)
    print("Testing receipt upload...")
    print("-"*60)
    
    response = requests.post(
        f"{base_url}/api/receipts/upload/",
        headers=headers,
        files=files,
        data=data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        print("✓ Receipt uploaded successfully!")
        receipt = response.json().get('receipt', {})
        print(f"Receipt ID: {receipt.get('id')}")
        print(f"File: {receipt.get('original_file_name')}")
        print(f"Amount: {receipt.get('amount')} {receipt.get('currency')}")
    else:
        print(f"✗ Upload failed: {response.text}")
    print("="*60)
    
except Exception as e:
    print(f"Upload test error: {e}")