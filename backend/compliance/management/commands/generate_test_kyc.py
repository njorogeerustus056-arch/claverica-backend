"""
compliance/management/commands/generate_test_kyc.py
Management command to generate test KYC data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from backend.compliance.models import (
    KYCVerification, KYCDocument, VerificationStatus,
    DocumentType, ComplianceLevel
)
import uuid
from datetime import timedelta



class Command(BaseCommand):
    help = 'Generate test KYC verification data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of KYC verifications to generate'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        
        # Create test users if they don't exist
        for i in range(count):
            user, created = get_user_model().objects.get_or_create(
                username=f'testuser{i+1}',
                defaults={
                    'email': f'test{i+1}@example.com',
                    'first_name': f'Test{i+1}',
                    'last_name': 'User'
                }
            )
            
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created test user: {user.username}'))
            
            # Create KYC verification
            verification = KYCVerification.objects.create(
                user_id=str(user.id),
                first_name=user.first_name,
                last_name=user.last_name,
                date_of_birth=timezone.now() - timedelta(days=365*25),
                nationality='US',
                country_of_residence='US',
                email=user.email,
                phone_number='+1234567890',
                address_line1='123 Main St',
                city='New York',
                postal_code='10001',
                id_number=f'ID{user.id}',
                id_type=DocumentType.PASSPORT,
                verification_status=VerificationStatus.APPROVED,
                compliance_level=ComplianceLevel.STANDARD,
                risk_score=10.0,
                risk_level='low',
                verified_at=timezone.now()
            )
            
            self.stdout.write(self.style.SUCCESS(
                f'Created KYC verification for {user.username} (ID: {verification.id})'
            ))
            
            # Create sample document
            KYCDocument.objects.create(
                verification=verification,
                user_id=str(user.id),
                document_type=DocumentType.PASSPORT,
                document_number=f'PASS{user.id}',
                file_name=f'passport_{user.id}.jpg',
                original_file_name='passport.jpg',
                file_path=f'uploads/kyc/{user.id}/passport.jpg',
                file_size=1024000,
                file_type='image/jpeg',
                status=VerificationStatus.APPROVED,
                verified_at=timezone.now()
            )
        
        self.stdout.write(self.style.SUCCESS(f'\nGenerated {count} test KYC verifications'))