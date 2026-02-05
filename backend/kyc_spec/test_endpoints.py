# kyc_spec/test_endpoints.py
"""
Test the new KYC Spec endpoints
"""
import os
import sys
import django
from pathlib import Path

# Setup
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import Client
import json

def test_endpoints():
    print("🧪 Testing KYC Spec Endpoints")
    print("=" * 60)
    
    client = Client()
    
    endpoints = [
        ('/api/kyc-spec/dashboard/', 'GET', None),
        ('/api/kyc-spec/summary/', 'GET', None),
        ('/api/kyc-spec/recent/', 'GET', None),
        ('/api/kyc-spec/search/?q=test', 'GET', None),
        ('/api/kyc-spec/export/?format=json', 'GET', None),
    ]
    
    for url, method, data in endpoints:
        print(f"\n🔗 Testing {method} {url}")
        try:
            if method == 'GET':
                response = client.get(url)
            elif method == 'POST':
                response = client.post(url, json.dumps(data), content_type='application/json')
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = json.loads(response.content)
                    if result.get('success'):
                        print(f"   ✅ Success: {result.get('message', 'OK')}")
                    else:
                        print(f"   ⚠️  Failed: {result.get('error', 'Unknown')}")
                except:
                    print(f"   📄 Response: {len(response.content)} bytes")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Exception: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Testing complete!")

if __name__ == '__main__':
    test_endpoints()