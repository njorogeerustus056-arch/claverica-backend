import sys, os
import subprocess

print("🚀 CLAVERICA PLATFORM - FINAL COMPREHENSIVE TEST")
print("=" * 60)

# Run all tests in sequence
tests = [
    ("System Status", "python system_status_summary.py"),
    ("Authentication", "python test_authentication.py"),
    ("Database Models", "python test_database_models.py"),
    ("API Endpoints", "python test_all_endpoints.py"),
    ("Email Config", "python test_email_config.py"),
    ("Business Modules", "python test_business_modules.py"),
]

results = []

for test_name, command in tests:
    print(f"\n🧪 RUNNING: {test_name}")
    print("-" * 40)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ {test_name}: PASSED")
            results.append((test_name, True))
            
            # Show last few lines of output
            lines = result.stdout.strip().split('\n')[-5:]
            for line in lines:
                print(f"   {line}")
        else:
            print(f"❌ {test_name}: FAILED")
            print(f"   Error: {result.stderr[:200]}")
            results.append((test_name, False))
            
    except subprocess.TimeoutExpired:
        print(f"⏱️  {test_name}: TIMEOUT")
        results.append((test_name, False))
    except Exception as e:
        print(f"💥 {test_name}: ERROR - {str(e)[:100]}")
        results.append((test_name, False))

print("\n" + "=" * 60)
print("📊 TEST RESULTS SUMMARY:")
print("=" * 60)

passed = sum(1 for _, success in results if success)
total = len(results)

for test_name, success in results:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"   {status} {test_name}")

print(f"\n🎯 OVERALL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

if passed == total:
    print("\n🎉🎉🎉 CLAVERICA PLATFORM IS PRODUCTION READY! 🎉🎉🎉")
    print("\n✅ All systems verified")
    print("✅ Business logic intact")
    print("✅ API endpoints working")
    print("✅ Database operational")
    print("✅ Authentication ready")
    print("✅ Email configured")
    print("\n🚀 READY FOR DEPLOYMENT!")
else:
    print(f"\n⚠️  {total - passed} tests need attention before deployment")
    print("   Review failed tests and fix issues")

print("\n📋 NEXT STEPS:")
print("   1. Fix any failed tests above")
print("   2. Run: python manage.py collectstatic --noinput")
print("   3. Push to GitHub from local machine")
print("   4. Let Render auto-deploy")
print("   5. Test live deployment")
