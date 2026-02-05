from rest_framework import serializers
from .models import Account
import re
from django.contrib.auth.password_validation import validate_password

class AccountRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for account registration with all signup fields"""
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = Account
        fields = [
            # Required fields
            'email', 'first_name', 'last_name', 'password', 'confirm_password', 'phone',

            # Optional personal fields (null=True, blank=True in model)
            'date_of_birth', 'gender',

            # Optional KYC fields
            'doc_type', 'doc_number', 'doc_country', 'doc_expiry_date',

            # Optional address fields
            'address_line1', 'city', 'state_province', 'postal_code', 'country',
            'country_of_residence', 'nationality',

            # Optional employment fields
            'occupation', 'employer', 'income_range'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'phone': {'required': True},
        }

    def validate_email(self, value):
        """Validate email is unique"""
        if Account.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def validate_phone(self, value):
        """Validate phone format (International)"""
        # International phone validation
        pattern = r'^\+[1-9]\d{1,14}$'  # E.164 format
        if not re.match(pattern, value.replace(' ', '')):
            raise serializers.ValidationError("Invalid phone number format. Use international format: +1234567890")
        return value

    def validate(self, data):
        """Validate passwords match"""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data

    def create(self, validated_data):
        """Create new account with activation code"""
        confirm_password = validated_data.pop('confirm_password', None)
        password = validated_data.pop('password')

        # Create account
        account = Account(**validated_data)
        account.set_password(password)
        account.is_active = False  # Inactive until verification
        account.is_verified = False
        account.save()

        # Generate and send activation code
        activation_code = account.generate_activation_code()
        account.send_activation_email()

        return account

class ActivationSerializer(serializers.Serializer):
    """Serializer for activation code verification"""
    email = serializers.EmailField()
    activation_code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, data):
        """Validate activation code"""
        try:
            account = Account.objects.get(email=data['email'])
        except Account.DoesNotExist:
            raise serializers.ValidationError({"email": "Account not found"})

        if account.is_verified:
            raise serializers.ValidationError({"email": "Account already verified"})

        if not account.activation_code:
            raise serializers.ValidationError({"activation_code": "No activation code found"})

        data['account'] = account
        return data

class ResendActivationSerializer(serializers.Serializer):
    """Serializer for resending activation code"""
    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate email exists and needs activation"""
        try:
            account = Account.objects.get(email=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account not found")

        if account.is_verified:
            raise serializers.ValidationError("Account already verified")

        return account  # Return account object for view to use

# ========== NEW PASSWORD SERIALIZERS ==========

class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Validate email exists (but don't reveal if it doesn't)"""
        value = value.strip().lower()
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(max_length=6, min_length=6, required=True)
    new_password = serializers.CharField(write_only=True, min_length=8, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        """Validate passwords match"""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })
        
        # Validate password strength
        try:
            validate_password(data['new_password'])
        except Exception as e:
            raise serializers.ValidationError({
                'new_password': list(e.messages) if hasattr(e, 'messages') else str(e)
            })
        
        return data
    
    def validate_otp(self, value):
        """Validate OTP format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing password"""
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, min_length=8, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_current_password(self, value):
        """Validate current password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value

    def validate(self, data):
        """Validate passwords"""
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError({
                'new_password': 'New password must be different from current password'
            })
        
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })
        
        # Validate password strength
        try:
            validate_password(data['new_password'])
        except Exception as e:
            raise serializers.ValidationError({
                'new_password': list(e.messages) if hasattr(e, 'messages') else str(e)
            })
        
        return data