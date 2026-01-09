# accounts/serializers.py - UPDATED
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

from .models import Account


class AccountRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = Account
        fields = ['email', 'first_name', 'last_name', 'password', 'confirm_password']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({"password": _("Passwords do not match.")})
        return attrs
    
    def create(self, validated_data):
        account = Account.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return account


class AccountLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            return attrs
        raise serializers.ValidationError(_("Must include 'email' and 'password'."))


class EmailVerificationOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(
        required=True,
        max_length=6,
        min_length=6,
        help_text="6-digit OTP sent to your email"
    )
    
    def validate(self, attrs):
        email = attrs.get('email')
        otp = attrs.get('otp')
        
        try:
            account = Account.objects.get(email=email)
        except Account.DoesNotExist:
            raise serializers.ValidationError(_("Account not found."))
        
        if account.email_verified:
            raise serializers.ValidationError(_("Email already verified."))
        
        # Check if OTP is valid
        if not account.is_otp_valid(otp, otp_type='email_verification'):
            account.increment_otp_attempts('email_verification')
            raise serializers.ValidationError(_("Invalid or expired OTP."))
        
        attrs['account'] = account
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetOTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(
        required=True,
        max_length=6,
        min_length=6,
        help_text="6-digit OTP sent to your email"
    )
    
    def validate(self, attrs):
        email = attrs.get('email')
        otp = attrs.get('otp')
        
        try:
            account = Account.objects.get(email=email)
        except Account.DoesNotExist:
            raise serializers.ValidationError(_("Account not found."))
        
        # Check if OTP is valid
        if not account.is_otp_valid(otp, otp_type='password_reset'):
            account.increment_otp_attempts('password_reset')
            raise serializers.ValidationError(_("Invalid or expired OTP."))
        
        attrs['account'] = account
        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(
        required=True,
        max_length=6,
        min_length=6,
        help_text="6-digit OTP sent to your email"
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        email = attrs.get('email')
        otp = attrs.get('otp')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        # Check passwords match
        if new_password != confirm_password:
            raise serializers.ValidationError({"password": _("Passwords do not match.")})
        
        try:
            account = Account.objects.get(email=email)
        except Account.DoesNotExist:
            raise serializers.ValidationError(_("Account not found."))
        
        # Verify OTP
        if not account.is_otp_valid(otp, otp_type='password_reset'):
            account.increment_otp_attempts('password_reset')
            raise serializers.ValidationError(_("Invalid or expired OTP."))
        
        attrs['account'] = account
        return attrs


class AccountProfileSerializer(serializers.ModelSerializer):
    """Minimal account info for authentication responses"""
    class Meta:
        model = Account
        fields = ['id', 'email', 'first_name', 'last_name', 'email_verified', 'date_joined']
        read_only_fields = ['id', 'email_verified', 'date_joined']