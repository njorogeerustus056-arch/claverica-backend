import requests
endpoints = [
    '/api/users/profile/',
    '/api/transactions/',
    '/api/notifications/notifications/',
    '/api/kyc/verifications/my_status/',
]
for e in endpoints:
    r = requests.get(f'https://claverica-backend-rniq.onrender.com{e}', timeout=5)
    print(f"{'✅' if r.status_code==200 else '❌'} {e}: {r.status_code}")
