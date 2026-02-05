import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()

from transfers.models import Transfer, TAC, TransferLog, TransferLimit

print("=== CURRENT TRANSFER APP DATA ===")
print(f"TransferLimit records: {TransferLimit.objects.count()}")
print(f"Transfer records: {Transfer.objects.count()}")
print(f"TAC records: {TAC.objects.count()}")
print(f"TransferLog records: {TransferLog.objects.count()}")

if Transfer.objects.count() > 0:
    print("\nRecent Transfers:")
    for transfer in Transfer.objects.all()[:5]:
        print(f"  {transfer.reference}: ${transfer.amount} to {transfer.recipient_name} ({transfer.status})")
        
if TAC.objects.count() > 0:
    print("\nRecent TACs:")
    for tac in TAC.objects.all()[:5]:
        print(f"  TAC {tac.code} for {tac.transfer.reference} ({tac.status})")
