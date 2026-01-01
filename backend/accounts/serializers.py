# accounts/serializers.py
from rest_framework import serializers
from .models import Account, AccountProfile, AccountSettings

class AccountSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Account
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "password",
            "phone",
            "document_type",
            "document_number",
            "street",
            "city",
            "state",
            "zip_code",
            "occupation",
            "employer",
            "income_range",
        ]
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "password": {"required": True},
            "phone": {"required": False},
            "document_type": {"required": False},
            "document_number": {"required": False},
            "street": {"required": False},
            "city": {"required": False},
            "state": {"required": False},
            "zip_code": {"required": False},
            "occupation": {"required": False},
            "employer": {"required": False},
            "income_range": {"required": False},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = Account.objects.create_user(password=password, **validated_data)
        return user

class AccountProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountProfile
        fields = '__all__'
        read_only_fields = ['account', 'created_at', 'updated_at']

class AccountSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSettings
        fields = '__all__'
        read_only_fields = ['account', 'created_at', 'updated_at']