"""
Quick test without Django dependencies
"""
import os
from pathlib import Path

def quick_test():
    print(" QUICK KYC SPEC FILE CHECK")
    print("=" * 50)
    
    base_dir = Path(__file__).resolve().parent.parent
    print(f"Project: {base_dir}")
    
    # Essential files that must exist
    essentials = [
        ('kyc_spec/models.py', 'Models file'),
        ('kyc_spec/views.py', 'Views file'),
        ('kyc_spec/urls.py', 'URLs file'),
        ('kyc_spec/services.py', 'Services file'),
        ('media/kyc_spec/logs/leads.csv', 'Leads CSV'),
        ('backend/settings.py', 'Main settings'),
        ('backend/urls.py', 'Main URLs'),
    ]
    
    for file_path, description in essentials:
        full_path = base_dir / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f" {description:20} {file_path} ({size} bytes)")
        else:
            print(f" {description:20} {file_path} - MISSING!")
    
    # Check if kyc_spec is in settings
    settings_path = base_dir / 'backend' / 'settings.py'
    if settings_path.exists():
        with open(settings_path, 'r') as f:
            content = f.read()
            if "'kyc_spec'" in content or '"kyc_spec"' in content:
                print(" kyc_spec in INSTALLED_APPS")
            else:
                print(" kyc_spec NOT in INSTALLED_APPS - Add to settings.py!")
    
    print("\n Quick test complete!")

if __name__ == '__main__':
    quick_test()
