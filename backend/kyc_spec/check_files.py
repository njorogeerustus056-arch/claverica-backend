import os
from pathlib import Path

def check_files():
    print("?? Checking KYC Spec setup...")
    print("=" * 50)
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    print(f"Project: {base_dir}")
    
    print("\n?? Checking directories:")
    dirs = [
        "media/kyc_spec/dumps/loan",
        "media/kyc_spec/dumps/insurance",
        "media/kyc_spec/dumps/escrow",
        "media/kyc_spec/logs",
        "media/kyc_spec/uploads"
    ]
    
    all_good = True
    for dir_path in dirs:
        full_path = base_dir / dir_path
        if full_path.exists():
            print(f"  ? {dir_path}")
        else:
            print(f"  ? {dir_path}")
            all_good = False
    
    print("\n?? Checking files:")
    files = [
        "media/kyc_spec/logs/leads.csv",
        "media/kyc_spec/logs/submissions.log",
        "backend/kyc_spec/storage/__init__.py",
        "backend/kyc_spec/management/__init__.py",
        "backend/kyc_spec/management/commands/__init__.py",
        "backend/kyc_spec/management/commands/init_kyc_spec_storage.py"
    ]
    
    for file_path in files:
        full_path = base_dir / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ? {file_path} ({size} bytes)")
        else:
            print(f"  ? {file_path}")
            all_good = False
    
    if all_good:
        print("\n?? All files are in place!")
        print("\nNext: Run migrations:")
        print("  python manage.py makemigrations kyc_spec")
        print("  python manage.py migrate kyc_spec")
    else:
        print("\n?? Some files are missing!")
    
    return all_good

if __name__ == "__main__":
    check_files()
