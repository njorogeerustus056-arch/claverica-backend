# kyc_spec/models.py
from django.db import models
from django.contrib.auth import get_user_model
import uuid
import os
from django.utils import timezone

User = get_user_model()

def get_dump_upload_path(instance, filename):
    """Generate upload path for dump files"""
    return f'kyc_spec/dumps/{instance.product_type}/{uuid.uuid4()}_{filename}'

class KycSpecDump(models.Model):
    """Simple model to store KYC dump data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Product info
    product_type = models.CharField(max_length=50, choices=[
        ('loan', 'Loan Application'),
        ('insurance', 'Insurance Application'),
        ('escrow', 'Escrow Application'),
    ])
    product_subtype = models.CharField(max_length=100, blank=True)  # e.g., 'health_insurance'
    
    # User contact info (in case user is not logged in)
    user_email = models.EmailField(blank=True)
    user_phone = models.CharField(max_length=20, blank=True)
    
    # Dump data
    raw_data = models.JSONField(default=dict)  # Store everything as JSON
    document_count = models.IntegerField(default=0)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    source = models.CharField(max_length=100, default='web')  # web, mobile, api
    
    # Status
    status = models.CharField(max_length=20, default='collected', choices=[
        ('collected', 'Collected'),
        ('processed', 'Processed'),
        ('contacted', 'Contacted'),
        ('converted', 'Converted'),
    ])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product_type', 'created_at']),
            models.Index(fields=['user_email']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.product_type} - {self.user_email or 'Anonymous'} - {self.created_at.date()}"
    
    def get_display_data(self):
        """Get cleaned data for display"""
        return {
            'id': str(self.id),
            'product': f"{self.product_type} - {self.product_subtype or 'General'}",
            'contact': self.user_email or self.user_phone or 'Anonymous',
            'status': self.status,
            'created': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'documents': self.document_count,
            'source': self.source
        }
    
    def get_time_since_creation(self):
        """Get human-readable time since creation"""
        now = timezone.now()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds // 3600 > 0:
            return f"{diff.seconds // 3600} hours ago"
        elif diff.seconds // 60 > 0:
            return f"{diff.seconds // 60} minutes ago"
        else:
            return "just now"
    
    def mark_as_contacted(self, notes=None, user=None):
        """Mark submission as contacted with optional notes"""
        self.status = 'contacted'
        
        if notes:
            current_data = self.raw_data or {}
            admin_notes = current_data.get('admin_notes', [])
            if not isinstance(admin_notes, list):
                admin_notes = []
            
            admin_notes.append({
                'note': notes,
                'action': 'contacted',
                'by': user.email if user and hasattr(user, 'email') else 'system',
                'at': timezone.now().isoformat()
            })
            current_data['admin_notes'] = admin_notes
            self.raw_data = current_data
        
        self.save()
        return True
    
    def get_admin_notes(self):
        """Get all admin notes from raw data"""
        if not self.raw_data:
            return []
        
        notes = self.raw_data.get('admin_notes', [])
        if isinstance(notes, list):
            return notes
        return []
    
    def add_admin_note(self, note, user=None):
        """Add a new admin note"""
        current_data = self.raw_data or {}
        admin_notes = current_data.get('admin_notes', [])
        if not isinstance(admin_notes, list):
            admin_notes = []
        
        admin_notes.append({
            'note': note,
            'by': user.email if user and hasattr(user, 'email') else 'system',
            'at': timezone.now().isoformat()
        })
        
        current_data['admin_notes'] = admin_notes
        self.raw_data = current_data
        self.save()
        return True
    
    def get_contact_info(self):
        """Get formatted contact information"""
        contact_info = []
        if self.user_email:
            contact_info.append(f"Email: {self.user_email}")
        if self.user_phone:
            contact_info.append(f"Phone: {self.user_phone}")
        if self.user:
            contact_info.append(f"User ID: {self.user.id}")
        
        return ", ".join(contact_info) if contact_info else "No contact info"
    
    def get_product_details(self):
        """Get formatted product details"""
        details = {
            'type': self.get_product_type_display(),
            'subtype': self.product_subtype or 'Not specified',
            'created': self.created_at.strftime('%b %d, %Y %I:%M %p'),
            'status': self.get_status_display(),
            'age': self.get_time_since_creation()
        }
        
        # Add any specific data from raw_data
        if self.raw_data:
            if 'amount' in self.raw_data:
                details['amount'] = self.raw_data['amount']
            if 'monthly_premium' in self.raw_data:
                details['monthly_premium'] = self.raw_data['monthly_premium']
            if 'plan_name' in self.raw_data:
                details['plan_name'] = self.raw_data['plan_name']
        
        return details