import re
with open('backend/settings.py') as f:
    content = f.read()

# Find INSTALLED_APPS section
match = re.search(r'INSTALLED_APPS\s*=\s*\[(.*?)\]', content, re.DOTALL)
if match:
    apps_section = match.group(1)
    apps = re.findall(r'["\']([^"\']+)["\']', apps_section)
    
    # Remove duplicates
    seen = set()
    unique = []
    for app in apps:
        if app not in seen:
            seen.add(app)
            unique.append(app)
    
    # Rebuild
    new_section = '\n    ' + ',\n    '.join(f'"{app}"' for app in unique) + '\n    '
    new_content = content.replace(apps_section, new_section)
    
    with open('backend/settings.py', 'w') as f:
        f.write(new_content)
    
    print(f"✅ Removed {len(apps)-len(unique)} duplicates")
else:
    print("❌ No INSTALLED_APPS found")
