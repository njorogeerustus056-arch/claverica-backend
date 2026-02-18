import uuid
import datetime as dt
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from django.apps import apps


class AccountManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)

        # Create the user instance
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

    def generate_account_number(self, account_instance):
        """Generate unique account number in format: CLV-XXX-DDMMYY-YY"""
        import random

        # Extract last 3 digits of phone
        phone_last_3 = account_instance.phone[-3:] if account_instance.phone else '000'

        # Handle date_of_birth - could be string or date object
        dob = account_instance.date_of_birth

        if dob:
            # If it's a string, parse it
            if isinstance(dob, str):
                try:
                    dob = dt.datetime.strptime(dob, '%Y-%m-%d').date()
                except ValueError:
                    dob = None
        else:
            dob = None

        # Generate random suffix
        random_suffix = ''.join(str(random.randint(0, 9)) for _ in range(2))

        # Format account number: CLV-XXX-DDMMYY-YY-RR
        if dob:
            account_number = f"CLV-{phone_last_3}-{dob.strftime('%d%m%y')}-{str(timezone.now().year)[-2:]}-{random_suffix}"
        else:
            # Use current date if DOB not available
            today = timezone.now().date()
            account_number = f"CLV-{phone_last_3}-{today.strftime('%d%m%y')}-{str(today.year)[-2:]}-{random_suffix}"

        return account_number


class Account(AbstractUser):
    """Custom user model with extended fields for international users"""

    # FIX: Add custom related_name to avoid conflicts with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='account_set',  # Changed from default 'user_set'
        related_query_name='account',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='account_set',  # Changed from default 'user_set'
        related_query_name='account',
    )

    objects = AccountManager()

    # Remove username, use email instead
    username = None
    email = models.EmailField(_('email address'), unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone', 'first_name', 'last_name']

    # Core Identity (from signup form)
    phone = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('non_binary', 'Non-binary'),
        ('transgender', 'Transgender'),
        ('genderqueer', 'Genderqueer'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say')
    ])

    # KYC Documentation (from signup form)
    doc_type = models.CharField(max_length=50, null=True, blank=True, choices=[
        ('passport', 'Passport'),
        ('national_id', 'National ID Card'),
        ('drivers_license', 'Driver\'s License'),
        ('residence_permit', 'Residence Permit')
    ])
    doc_number = models.CharField(max_length=50, null=True, blank=True)
    doc_country = models.CharField(max_length=100, null=True, blank=True)
    doc_expiry_date = models.DateField(null=True, blank=True)
    doc_front_image = models.ImageField(upload_to='kyc_docs/', null=True, blank=True)
    doc_back_image = models.ImageField(upload_to='kyc_docs/', null=True, blank=True)
    doc_selfie_image = models.ImageField(upload_to='kyc_selfies/', null=True, blank=True)

    # Address Information (from signup form)
    address_line1 = models.CharField(max_length=255, null=True, blank=True)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state_province = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    country_of_residence = models.CharField(max_length=100, null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)

    # Employment Information (from signup form)
    occupation = models.CharField(max_length=100, null=True, blank=True)
    employer = models.CharField(max_length=100, null=True, blank=True)
    income_range = models.CharField(max_length=50, null=True, blank=True, choices=[
        ('<10000', 'Below $10,000 / 9,000 / 8,000'),
        ('10000-30000', '$10,000 - $30,000 / 9,000 - 27,000'),
        ('30000-50000', '$30,000 - $50,000 / 27,000 - 45,000'),
        ('50000-75000', '$50,000 - $75,000 / 45,000 - 68,000'),
        ('75000-100000', '$75,000 - $100,000 / 68,000 - 90,000'),
        ('100000-150000', '$100,000 - $150,000 / 90,000 - 135,000'),
        ('150000-200000', '$150,000 - $200,000 / 135,000 - 180,000'),
        ('>200000', 'Above $200,000 / 180,000 / 160,000')
    ])

    # Account Status Fields
    account_number = models.CharField(max_length=50, unique=True, null=True, blank=True, editable=False)
    is_verified = models.BooleanField(default=False)
    account_status = models.CharField(max_length=20, default='active', choices=[
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
        ('dormant', 'Dormant')
    ])
    kyc_status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ])
    risk_level = models.CharField(max_length=20, default='low', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ])

    # Activation system
    activation_code = models.CharField(max_length=6, null=True, blank=True)
    activation_code_sent_at = models.DateTimeField(null=True, blank=True)
    activation_code_expires_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'

    def generate_activation_code(self):
        """Generate a 6-digit activation code"""
        import random
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.activation_code = code
        self.activation_code_sent_at = timezone.now()
        self.activation_code_expires_at = timezone.now() + timedelta(hours=24)
        self.save(update_fields=['activation_code', 'activation_code_sent_at', 'activation_code_expires_at'])
        return code

    def send_activation_email(self):
        """This method is deprecated - email is now sent from views asynchronously"""
        # Just log that this was called (should not happen in production)
        logger = logging.getLogger(__name__)
        logger.warning(f"send_activation_email called directly for {self.email} - should use async view method instead")
        return True

    def verify_activation_code(self, code):
        """Verify activation code"""
        if not self.activation_code:
            return False, "No activation code found"

        if self.activation_code != code:
            return False, "Invalid activation code"

        if timezone.now() > self.activation_code_expires_at:
            return False, "Activation code has expired"

        # Code is valid - activate account
        self.is_active = True
        self.is_verified = True
        self.activation_code = None
        self.save(update_fields=['is_active', 'is_verified', 'activation_code'])
        return True, "Account activated successfully"

    def __str__(self):
        return f"{self.email} ({self.account_number or 'No account number'})"

    def save(self, *args, **kwargs):
        if not self.account_number and self.is_verified:
            self.account_number = Account.objects.generate_account_number(self)
        super().save(*args, **kwargs)