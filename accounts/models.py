from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission

# -----------------------------
# Custom User Manager
# -----------------------------
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
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, first_name, last_name, password, **extra_fields)

# -----------------------------
# Account Model
# -----------------------------
class Account(AbstractBaseUser, PermissionsMixin):
    # Personal Info
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Document Info
    DOC_TYPE_CHOICES = [
        ('drivers-license', "Driver's License"),
        ('ssn', "SSN"),
        ('tfn', "TFN"),
        ('national-id', "National ID"),
        ('passport', "Passport"),
    ]
    document_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, blank=True, null=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)

    # Address
    street = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)

    # Employment (optional)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    employer = models.CharField(max_length=100, blank=True, null=True)
    INCOME_RANGE_CHOICES = [
        ('<25k', 'Below $25,000'),
        ('25k-50k', '$25,000 – $50,000'),
        ('50k-100k', '$50,000 – $100,000'),
        ('100k-200k', '$100,000 – $200,000'),
        ('>200k', 'Above $200,000'),
    ]
    income_range = models.CharField(max_length=20, choices=INCOME_RANGE_CHOICES, blank=True, null=True)

    # Permissions / Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Override PermissionsMixin fields to avoid clashes
    groups = models.ManyToManyField(
        Group,
        related_name='account_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='account_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    objects = AccountManager()

    # Authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
