# compare_environments.py
import requests
import json

print("🔍 COMPARING LOCALHOST vs RENDER")
print("=" * 60)

# Test Localhost
print("\n1. LOCALHOST (127.0.0.1:8000):")
try:
    local_response = requests.get("http://localhost:8000/api/debug/user-model/", timeout=5)
    if local_response.status_code == 200:
        local_data = local_response.json()
        print(f"   ✅ User Model: {local_data.get('ACTUAL_USER_MODEL')}")
        print(f"   ✅ Is Custom: {local_data.get('IS_CUSTOM_MODEL')}")
        print(f"   ✅ Accounts Position: {local_data.get('APP_ORDER', {}).get('accounts_position')}")
        local_model = local_data.get('ACTUAL_USER_MODEL')
    else:
        print(f"   ❌ Status: {local_response.status_code}")
        print(f"   Response: {local_response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test Render
print("\n2. RENDER (claverica-backend.onrender.com):")
try:
    render_response = requests.get("https://claverica-backend.onrender.com/api/debug/user-model/", timeout=30)
    if render_response.status_code == 200:
        render_data = render_response.json()
        print(f"   ✅ User Model: {render_data.get('ACTUAL_USER_MODEL')}")
        print(f"   ✅ Is Custom: {render_data.get('IS_CUSTOM_MODEL')}")
        print(f"   ✅ Accounts Position: {render_data.get('APP_ORDER', {}).get('accounts_position')}")
        print(f"   ✅ Is Render: {render_data.get('IS_RENDER')}")
        print(f"   ✅ Is Production: {render_data.get('IS_PRODUCTION')}")
        render_model = render_data.get('ACTUAL_USER_MODEL')
    else:
        print(f"   ❌ Status: {render_response.status_code}")
        print(f"   Response: {render_response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("📊 COMPARISON SUMMARY:")

if 'local_model' in locals() and 'render_model' in locals():
    if local_model == render_model:
        print("✅ User models MATCH!")
    else:
        print("❌ User models DIFFERENT!")
        print(f"   Local: {local_model}")
        print(f"   Render: {render_model}")
        
    # Check positions
    local_pos = local_data.get('APP_ORDER', {}).get('accounts_position')
    render_pos = render_data.get('APP_ORDER', {}).get('accounts_position')
    print(f"\n📌 Accounts App Position:")
    print(f"   Local: {local_pos}")
    print(f"   Render: {render_pos}")

print("\n" + "=" * 60)
print("🎯 NEXT STEPS:")
print("1. Check Render logs for build errors")
print("2. Verify environment variables on Render")
print("3. Check database migrations on Render")
print("=" * 60)