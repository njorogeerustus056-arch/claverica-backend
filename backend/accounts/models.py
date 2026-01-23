# accounts/models.py - UPDATED
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import secrets
import string
from datetime import timedelta


class AccountManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Users must have an email address"))
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, first_name, last_name, password, **extra_fields)


class Account(AbstractBaseUser, PermissionsMixin):
    # Authentication fields ONLY
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=50)
    last_name = models.CharField(_('last name'), max_length=50)
    
    # Authentication status fields
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_superuser = models.BooleanField(_('superuser status'), default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)
    
    # Email verification with OTP
    email_verified = models.BooleanField(_('email verified'), default=False)
    email_verification_otp = models.CharField(max_length=6, blank=True, null=True)
    email_verification_otp_sent_at = models.DateTimeField(blank=True, null=True)
    email_verification_attempts = models.IntegerField(default=0)
    
    # Password reset with OTP
    password_reset_otp = models.CharField(max_length=6, blank=True, null=True)
    password_reset_otp_sent_at = models.DateTimeField(blank=True, null=True)
    password_reset_attempts = models.IntegerField(default=0)
    
    # Two-factor authentication (optional)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    
    objects = AccountManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _('account')
        verbose_name_plural = _('accounts')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['email_verified']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_short_name(self):
        return self.first_name
    
    # OTP Generation Methods
    def generate_otp(self, length=6):
        """Generate a numeric OTP"""
        digits = string.digits
        return ''.join(secrets.choice(digits) for _ in range(length))
    
    def generate_email_verification_otp(self):
        """Generate and save email verification OTP"""
        self.email_verification_otp = self.generate_otp()
        self.email_verification_otp_sent_at = timezone.now()
        self.email_verification_attempts = 0
        self.save(update_fields=[
            'email_verification_otp', 
            'email_verification_otp_sent_at',
            'email_verification_attempts'
        ])
        return self.email_verification_otp
    
    def generate_password_reset_otp(self):
        """Generate and save password reset OTP"""
        self.password_reset_otp = self.generate_otp()
        self.password_reset_otp_sent_at = timezone.now()
        self.password_reset_attempts = 0
        self.save(update_fields=[
            'password_reset_otp', 
            'password_reset_otp_sent_at',
            'password_reset_attempts'
        ])
        return self.password_reset_otp
    
    def is_otp_valid(self, otp, otp_type='email_verification', expiry_minutes=10):
        """Check if OTP is valid and not expired"""
        if otp_type == 'email_verification':
            otp_field = self.email_verification_otp
            sent_at = self.email_verification_otp_sent_at
            attempts_field = 'email_verification_attempts'
        elif otp_type == 'password_reset':
            otp_field = self.password_reset_otp
            sent_at = self.password_reset_otp_sent_at
            attempts_field = 'password_reset_attempts'
        else:
            return False
        
        if not otp_field or not sent_at:
            return False
        
        # Check expiry
        expiry_time = sent_at + timedelta(minutes=expiry_minutes)
        if timezone.now() > expiry_time:
            return False
        
        # Check attempts
        if getattr(self, attempts_field) >= 5:
            return False
        
        return otp_field == otp
    
    def increment_otp_attempts(self, otp_type='email_verification'):
        """Increment OTP attempts counter"""
        if otp_type == 'email_verification':
            self.email_verification_attempts += 1
            self.save(update_fields=['email_verification_attempts'])
        elif otp_type == 'password_reset':
            self.password_reset_attempts += 1
            self.save(update_fields=['password_reset_attempts'])
    
    def clear_otp(self, otp_type='email_verification'):
        """Clear OTP after successful verification"""
        if otp_type == 'email_verification':
            self.email_verification_otp = None
            self.email_verification_otp_sent_at = None
            self.email_verification_attempts = 0
            self.save(update_fields=[
                'email_verification_otp',
                'email_verification_otp_sent_at',
                'email_verification_attempts'
            ])
        elif otp_type == 'password_reset':
            self.password_reset_otp = None
            self.password_reset_otp_sent_at = None
            self.password_reset_attempts = 0
            self.save(update_fields=[
                'password_reset_otp',
                'password_reset_otp_sent_at',
                'password_reset_attempts'
            ])