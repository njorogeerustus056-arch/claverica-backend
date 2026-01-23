import requests
import json
import time

print("🚀 COMPLETE API ENDPOINT TEST")
print("="*60)

# Step 1: Get fresh token
print("\n🔐 Getting fresh JWT token...")
login_response = requests.post(
    "http://127.0.0.1:8000/api/auth/token/",
    json={"email": "eruznyaga001@gmail.com", "password": "38876879Eruz"}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.text}")
    exit()

tokens = login_response.json()
access_token = tokens['access']
headers = {"Authorization": f"Bearer {access_token}"}

print(f"✅ Token acquired: {access_token[:50]}...")

# Step 2: Define ALL endpoints to test
endpoints = [
    # Authentication (public)
    ("POST", "/api/auth/token/verify/", "Verify Token"),
    
    # User Management (protected)
    ("GET", "/api/users/profile/", "User Profile"),
    ("GET", "/api/users/profile-settings/", "Profile Settings"),
    ("GET", "/api/users/settings/", "User Settings"),
    ("GET", "/api/users/security-alerts/", "Security Alerts"),
    ("GET", "/api/users/security-score/", "Security Score"),
    ("GET", "/api/users/devices/", "Connected Devices"),
    ("GET", "/api/users/activity-logs/", "Activity Logs"),
    
    # Feature APIs (protected)
    ("GET", "/api/tasks/", "Tasks"),
    ("GET", "/api/cards/", "Cards"),
    ("GET", "/api/compliance/", "Compliance"),
    ("GET", "/api/crypto/", "Crypto"),
    ("GET", "/api/escrow/", "Escrow"),
    ("GET", "/api/notifications/", "Notifications"),
    ("GET", "/api/payments/", "Payments"),
    ("GET", "/api/receipts/", "Receipts"),
    ("GET", "/api/transactions/", "Transactions"),
    ("GET", "/api/transfers/", "Transfers"),
    
    # Public endpoints
    ("GET", "/", "API Root"),
    ("GET", "/health/", "Health Check"),
]

# Step 3: Test each endpoint
print(f"\n🧪 Testing {len(endpoints)} endpoints...")
print("="*60)

results = []
for method, endpoint, name in endpoints:
    try:
        url = f"http://127.0.0.1:8000{endpoint}"
        
        # Determine if endpoint needs authentication
        if endpoint.startswith(("/api/users/", "/api/tasks/", "/api/cards/", "/api/compliance/", 
                              "/api/crypto/", "/api/escrow/", "/api/notifications/", "/api/payments/",
                              "/api/receipts/", "/api/transfers/")):
            # Protected endpoint
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=5)
            elif method == "POST":
                response = requests.post(url, headers=headers, timeout=5)
        else:
            # Public endpoint
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, timeout=5)
        
        status_emoji = "✅" if response.status_code in [200, 201] else "⚠️"
        results.append((name, response.status_code))
        
        print(f"\n{status_emoji} {name}")
        print(f"   Method: {method}")
        print(f"   Endpoint: {endpoint}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            try:
                data = response.json()
                if isinstance(data, dict):
                    print(f"   Response keys: {list(data.keys())[:5]}")
                elif isinstance(data, list):
                    print(f"   Items returned: {len(data)}")
            except:
                print(f"   Response: {response.text[:100]}...")
        elif response.status_code == 401:
            print("   ⚠️ Requires authentication")
        elif response.status_code == 404:
            print("   ⚠️ Endpoint not found")
        
        # Small delay to avoid rate limiting
        time.sleep(0.3)
        
    except Exception as e:
        print(f"\n❌ {name} - Error: {e}")
        results.append((name, "ERROR"))

# Step 4: Summary
print("\n" + "="*60)
print("📊 TEST RESULTS SUMMARY")
print("="*60)

success = sum(1 for _, status in results if status in [200, 201])
total = len(results)

print(f"\n✅ Success: {success}/{total} endpoints")
print(f"⚠️  Issues: {total - success}/{total} endpoints")

print("\n🔍 Detailed Results:")
for name, status in results:
    if status in [200, 201]:
        print(f"  ✅ {name}: {status}")
    else:
        print(f"  ⚠️  {name}: {status}")

print("\n" + "="*60)
print("🎉 BACKEND TEST COMPLETE!")
print("="*60)