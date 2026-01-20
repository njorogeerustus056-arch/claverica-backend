import os
import re

# Find all admin.py files
for root, dirs, files in os.walk('.'):
    for file in files:
        if file == 'admin.py':
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Check if this file mentions Account
            if 'Account' in content or 'accounts' in root.lower():
                print(f"🔍 Found: {filepath}")
                
                # Fix the field names
                new_content = content.replace("'email_verification_token'", "'email_verification_otp'")
                new_content = new_content.replace("'email_verification_sent_at'", "'email_verification_otp_sent_at'")
                new_content = new_content.replace('email_verification_token', 'email_verification_otp')
                new_content = new_content.replace('email_verification_sent_at', 'email_verification_otp_sent_at')
                
                if new_content != content:
                    print(f"✅ Fixed field names in {filepath}")
                    
                    # Backup original
                    backup = filepath + '.backup'
                    with open(backup, 'w') as f:
                        f.write(content)
                    
                    # Write fixed content
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                else:
                    print(f"✅ No changes needed for {filepath}")
