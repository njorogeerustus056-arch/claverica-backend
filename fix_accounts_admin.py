import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claverica.settings')
django.setup()

# Find the accounts admin file
accounts_dir = os.path.join(os.getcwd(), 'accounts')
admin_file = os.path.join(accounts_dir, 'admin.py')

if os.path.exists(admin_file):
    print(f"📁 Found accounts admin.py at: {admin_file}")
    
    # Read the current content
    with open(admin_file, 'r') as f:
        content = f.read()
    
    # Check if the problematic fields are mentioned
    if 'email_verification_token' in content or 'email_verification_sent_at' in content:
        print("⚠️  Found problematic fields in admin.py")
        
        # Create backup
        backup_file = admin_file + '.backup'
        with open(backup_file, 'w') as f:
            f.write(content)
        print(f"✅ Created backup: {backup_file}")
        
        # Simple fix: remove problematic fields from fieldsets/list_display
        fixed_content = content.replace("'email_verification_token', ", '')
        fixed_content = fixed_content.replace("'email_verification_sent_at', ", '')
        fixed_content = fixed_content.replace('email_verification_token, ', '')
        fixed_content = fixed_content.replace('email_verification_sent_at, ', '')
        
        # Also check for fields attribute
        import re
        # Remove from fieldsets
        fixed_content = re.sub(r"fieldsets\s*=\s*\[[^\]]*'email_verification_token'[^\]]*\]", 
                              "fieldsets = [\n        (None, {'fields': ('email', 'password')}),\n        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),\n        ('Important dates', {'fields': ('last_login', 'date_joined')}),\n    ]", 
                              fixed_content)
        
        with open(admin_file, 'w') as f:
            f.write(fixed_content)
        
        print("✅ Updated admin.py - removed problematic fields")
        print("📋 New content preview:")
        print("-" * 50)
        print(fixed_content[:500])
        print("-" * 50)
    else:
        print("✅ admin.py doesn't contain problematic fields")
else:
    print(f"❌ Could not find accounts admin.py at: {accounts_dir}")
    
    # Try to find it
    import glob
    admin_files = list(glob.glob('**/admin.py', recursive=True))
    print(f"\n🔍 Searching for admin.py files... Found: {len(admin_files)}")
    for file in admin_files[:5]:
        print(f"  • {file}")
