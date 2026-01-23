import re

with open('backend/accounts/views.py', 'r') as f:
    content = f.read()

# Find CustomTokenObtainPairSerializer and comment it out
lines = content.split('\n')
new_lines = []
in_custom_serializer = False

for line in lines:
    if 'class CustomTokenObtainPairSerializer' in line:
        print("Found custom serializer - commenting out")
        new_lines.append('# ' + line)
        in_custom_serializer = True
    elif in_custom_serializer and line.strip() == '' and 'class ' in lines[lines.index(line)+1] if lines.index(line)+1 < len(lines) else False:
        new_lines.append(line)
        in_custom_serializer = False
    elif in_custom_serializer:
        new_lines.append('# ' + line)
    else:
        new_lines.append(line)

with open('backend/accounts/views.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("✅ Commented out CustomTokenObtainPairSerializer")
