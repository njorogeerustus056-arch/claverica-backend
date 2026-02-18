import os
import json
from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from .models import KycSpecDump

class KycSpecDumpService:
    """Service layer for handling KYC dump operations"""
    
    @staticmethod
    def create_dump(user, data, request=None):
        """Create a new KYC dump entry"""
        
        # Extract data with defaults
        product_type = data.get('product', 'unknown')
        product_subtype = data.get('product_subtype', '')
        
        # Get user contact info
        user_email = data.get('user_email', '')
        user_phone = data.get('user_phone', '')
        
        # If user is authenticated but no email provided, use user's email
        if user and not user_email and hasattr(user, 'email'):
            user_email = user.email
        
        # Count documents
        documents = data.get('documents', [])
        document_count = len(documents) if isinstance(documents, list) else 0
        
        # Get request metadata
        ip_address = None
        user_agent = ''
        if request:
            ip_address = KycSpecDumpService._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create the dump
        dump = KycSpecDump.objects.create(
            user=user if user and user.is_authenticated else None,
            product_type=product_type,
            product_subtype=product_subtype,
            user_email=user_email,
            user_phone=user_phone,
            raw_data=data,
            document_count=document_count,
            ip_address=ip_address,
            user_agent=user_agent,
            source=data.get('source', 'web'),
            status='collected'
        )
        
        # Save raw JSON to file system (backup)
        KycSpecDumpService._save_raw_json(dump, data)
        
        return dump
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def _save_raw_json(dump, data):
        """Save raw JSON to file system as backup"""
        try:
            dump_dir = os.path.join(
                settings.MEDIA_ROOT, 
                'kyc_spec', 
                'dumps', 
                dump.product_type,
                dump.created_at.strftime('%Y-%m-%d')
            )
            os.makedirs(dump_dir, exist_ok=True)
            
            filename = f"{dump.id}.json"
            filepath = os.path.join(dump_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'dump_id': str(dump.id),
                    'timestamp': dump.created_at.isoformat(),
                    'data': data
                }, f, indent=2, default=str)
        except Exception as e:
            # Silently fail - database is primary storage
            pass
