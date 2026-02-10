import os

print("🔍 CURRENT EMAIL CONFIGURATION")
print("=" * 40)

email_vars = [
    'EMAIL_BACKEND',
    'EMAIL_HOST', 
    'EMAIL_HOST_USER',
    'EMAIL_HOST_PASSWORD',
    'EMAIL_PORT',
    'EMAIL_USE_TLS',
    'EMAIL_USE_SSL',
    'DEFAULT_FROM_EMAIL'
]

for var in email_vars:
    value = os.environ.get(var, 'NOT SET')
    # Hide password value
    if 'PASSWORD' in var and value != 'NOT SET':
        value = '**** SET ****'
    print(f"{var}: {value}")

print("\n📧 Testing email backend...")
try:
    from django.core.mail import get_connection
    conn = get_connection()
    print(f"Email backend: {conn.__class__.__name__}")
except Exception as e:
    print(f"Error getting connection: {e}")
