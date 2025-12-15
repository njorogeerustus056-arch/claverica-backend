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
        # Optional fields: ensure empty strings instead of None
        optional_fields = [
            "phone", "document_type", "document_number",
            "street", "city", "state", "zip_code",
            "occupation", "employer", "income_range"
        ]
        for field in optional_fields:
            validated_data[field] = validated_data.get(field, "")

        # Use your custom Account manager to create the user
        user = Account.objects.create_user(**validated_data)
        return user
