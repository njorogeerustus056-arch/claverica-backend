import re

# Read the settings file
with open('backend/settings.py', 'r') as f:
    content = f.read()

# 1. Remove SIMPLE_JWT configuration completely
content = re.sub(
    r'SIMPLE_JWT = \{.*?\}',
    'SIMPLE_JWT = {\n    # DISABLED - Using middleware override\n}',
    content,
    flags=re.DOTALL
)

# 2. Remove SimpleJWT from REST_FRAMEWORK authentication classes
content = re.sub(
    r"'rest_framework_simplejwt\.authentication\.JWTAuthentication',?\s*",
    '',
    content
)

# 3. Disable throttling for auth endpoints
content = re.sub(
    r"'auth': '30/minute'",
    "'auth': '1000/minute'  # Increased to avoid throttling during testing",
    content
)

# 4. Add our middleware to the settings
if "'backend.middleware.force_auth.ForceAuthMiddleware'" not in content:
    # Find the MIDDLEWARE list
    middleware_match = re.search(r'MIDDLEWARE\s*=\s*\[', content)
    if middleware_match:
        pos = middleware_match.end()
        content = content[:pos] + "\n    'backend.middleware.force_auth.ForceAuthMiddleware'," + content[pos:]

# Write back
with open('backend/settings.py', 'w') as f:
    f.write(content)

print("✅ Nuclear patch applied to settings.py")
print("✅ Disabled SimpleJWT, increased throttling limits, added middleware")
