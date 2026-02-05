import os
import sys
from pathlib import Path

# Add the correct paths
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(current_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

try:
    import django
    django.setup()
    
    from kyc_spec.models import KycSpecDump
    
    print("? DATABASE CONNECTION SUCCESSFUL")
    print("=" * 50)
    
    count = KycSpecDump.objects.count()
    print(f"Total submissions in database: {count}")
    
    if count > 0:
        print("\n?? All submissions:")
        print("-" * 40)
        for dump in KycSpecDump.objects.all().order_by('-created_at'):
            print(f"""
  ID: {dump.id}
  Product: {dump.product_type} / {dump.product_subtype or 'N/A'}
  User: {dump.user_email or 'Anonymous'}
  Status: {dump.status}
  Created: {dump.created_at}
  Documents: {dump.document_count}
  Raw data keys: {list(dump.raw_data.keys()) if dump.raw_data else 'None'}
            """)
            
        # Summary
        print("\n?? Summary:")
        for product in ['loan', 'insurance', 'escrow']:
            count = KycSpecDump.objects.filter(product_type=product).count()
            print(f"  {product.upper()}: {count} submissions")
            
except Exception as e:
    print(f"? Error: {e}")
    print("\n?? Tip: Run this from the backend directory:")
    print("    cd backend")
    print("    python manage.py shell")
    print("\nThen run:")
    print("    from kyc_spec.models import KycSpecDump")
    print("    print(KycSpecDump.objects.count())")
