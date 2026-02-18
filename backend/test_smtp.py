import smtplib
import ssl
import os

print(" Testing Hostinger SMTP connection...")
print("=" * 40)

try:
    # Hostinger SMTP settings
    smtp_server = "smtp.hostinger.com"
    port = 465
    sender_email = "noreply@claverica.com"
    password = "38876879Eruz"
    
    print(f"Connecting to {smtp_server}:{port}...")
    
    # Create SSL context
    context = ssl.create_default_context()
    
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        print(" SSL connection established")
        
        try:
            server.login(sender_email, password)
            print(" Login successful!")
            print(" SMTP configuration is CORRECT")
            print("\n Email should work!")
        except Exception as login_error:
            print(f" Login failed: {login_error}")
            print("\nPossible issues:")
            print("1. Wrong password")
            print("2. Email not configured in Hostinger")
            print("3. SMTP not enabled in Hostinger")
            print("4. Two-factor authentication enabled")
            
except Exception as e:
    print(f" Connection failed: {e}")
    print("\nCheck:")
    print("1. Is Hostinger SMTP enabled?")
    print("2. Is port 465 open?")
    print("3. Are credentials correct?")
