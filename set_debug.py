import re
with open('backend/settings.py', 'r') as f:
    content = f.read()

# Replace DEBUG setting
content = re.sub(r'DEBUG\s*=\s*False', 'DEBUG = True', content)
content = re.sub(r'DEBUG\s*=\s*True', 'DEBUG = True', content)  # Ensure it's True

with open('backend/settings.py', 'w') as f:
    f.write(content)
print("✅ Set DEBUG = True")
