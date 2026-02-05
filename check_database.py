import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from kyc_spec.models import KycSpecDump

print("?? KYC SPEC SUBMISSIONS DATABASE")
print("=" * 50)

count = KycSpecDump.objects.count()
print(f"Total submissions: {count}")

if count > 0:
    print("\n?? Recent submissions:")
    for dump in KycSpecDump.objects.all().order_by('-created_at'):
        print(f"""
  ID: {dump.id}
  Product: {dump.product_type} ({dump.product_subtype or 'N/A'})
  Email: {dump.user_email or 'N/A'}
  Phone: {dump.user_phone or 'N/A'}
  Documents: {dump.document_count}
  Status: {dump.status}
  Created: {dump.created_at}
  Source: {dump.source}
  IP: {dump.ip_address or 'N/A'}
  """)
        
    # Summary by product
    print("\n?? Summary by product:")
    for product in ['loan', 'insurance', 'escrow']:
        product_count = KycSpecDump.objects.filter(product_type=product).count()
        print(f"  {product}: {product_count}")
else:
    print("No submissions found in database.")
