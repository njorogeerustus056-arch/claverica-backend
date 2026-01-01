from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .models import KYCVerification, TACCode, VerificationStatus, DocumentType
from .services import generate_tac_code


class KYCVerificationTestCase(TestCase):
    def setUp(self):
        self.verification = KYCVerification.objects.create(
            user_id="test_user_123",
            first_name="John",
            last_name="Doe",
            date_of_birth=timezone.now() - timedelta(days=365*25),
            nationality="US",
            country_of_residence="US",
            email="john@example.com",
            phone_number="+1234567890",
            address_line1="123 Main St",
            city="New York",
            postal_code="10001",
            id_number="ABC123456",
            id_type=DocumentType.PASSPORT
        )
    
    def test_verification_creation(self):
        """Test KYC verification is created correctly"""
        self.assertEqual(self.verification.user_id, "test_user_123")
        self.assertEqual(self.verification.verification_status, VerificationStatus.PENDING)
        self.assertEqual(self.verification.risk_level, "low")
    
    def test_verification_status_change(self):
        """Test changing verification status"""
        self.verification.verification_status = VerificationStatus.APPROVED
        self.verification.verified_at = timezone.now()
        self.verification.save()
        
        self.assertEqual(self.verification.verification_status, VerificationStatus.APPROVED)
        self.assertIsNotNone(self.verification.verified_at)


class TACCodeTestCase(TestCase):
    def test_tac_generation(self):
        """Test TAC code generation"""
        code = generate_tac_code()
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
    
    def test_tac_creation(self):
        """Test TAC code creation"""
        tac = TACCode.objects.create(
            user_id="test_user_123",
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        
        self.assertFalse(tac.is_used)
        self.assertFalse(tac.is_expired)
        self.assertEqual(tac.attempts, 0)
    
    def test_tac_expiry(self):
        """Test TAC code expiry"""
        tac = TACCode.objects.create(
            user_id="test_user_123",
            code="123456",
            expires_at=timezone.now() - timedelta(minutes=1)  # Already expired
        )
        
        self.assertTrue(tac.expires_at < timezone.now())
