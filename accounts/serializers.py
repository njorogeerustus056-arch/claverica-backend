# accounts/serializers.py
from rest_framework import serializers
from .models import Account

class AccountSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

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

    def create(self, validated_data):
        user = Account.objects.create_user(**validated_data)
        return user
