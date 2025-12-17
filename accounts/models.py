from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# Custom User Manager
class AccountManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, first_name, last_name, password, **extra_fields)

# Account Model
class Account(AbstractBaseUser, PermissionsMixin):
    # Personal Info
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Document Info
    doc_type_choices = [
        ('drivers-license', "Driver's License"),
        ('ssn', "SSN"),
        ('tfn', "TFN"),
        ('national-id', "National ID"),
        ('passport', "Passport"),
    ]
    document_type = models.CharField(max_length=20, choices=doc_type_choices)
    document_number = models.CharField(max_length=50)

    # Address
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)

    # Employment (optional)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    employer = models.CharField(max_length=100, blank=True, null=True)
    income_range_choices = [
        ('<25k', 'Below $25,000'),
        ('25k-50k', '$25,000 – $50,000'),
        ('50k-100k', '$50,000 – $100,000'),
        ('100k-200k', '$100,000 – $200,000'),
        ('>200k', 'Above $200,000'),
    ]
    income_range = models.CharField(max_length=20, choices=income_range_choices, blank=True, null=True)

    # Permissions / Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = AccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
