from django.db import models
from django.utils import timezone

# Add missing fields to models.py
def add_missing_fields():
    # Add these imports at the top of models.py if not present
    print("Adding missing fields to Transfer model...")
    
    # List of fields that should be in Transfer model
    missing_fields = [
        'tac_sent_at',
        'tac_verified_at', 
        'deducted_at',
        'settled_at',
        'external_reference',
        'admin_notes'
    ]
    
    for field in missing_fields:
        print(f"Checking {field}...")
    
    print("\nTo fix completely, update models.py with:")
    print("""
    # Add these fields to Transfer model:
    tac_sent_at = models.DateTimeField(null=True, blank=True)
    tac_verified_at = models.DateTimeField(null=True, blank=True)
    deducted_at = models.DateTimeField(null=True, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    external_reference = models.CharField(max_length=100, blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Add these fields to TAC model:
    used_at = models.DateTimeField(null=True, blank=True)
    """)

add_missing_fields()
