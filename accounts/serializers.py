from rest_framework import serializers
from .models import Account


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
            "document_type": {"required": True},
            "document_number": {"required": True},
            "street": {"required": True},
            "city": {"required": True},
            "state": {"required": True},
            "zip_code": {"required": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")

        # Create user via custom manager
        user = Account.objects.create_user(
            password=password,
            **validated_data
        )

        return user
