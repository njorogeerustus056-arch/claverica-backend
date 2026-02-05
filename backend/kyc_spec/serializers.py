# kyc_spec/serializers.py
from rest_framework import serializers

class KycSpecCollectSerializer(serializers.Serializer):
    """Serializer for collecting KYC dump data"""
    product = serializers.CharField(max_length=50, required=True)
    product_subtype = serializers.CharField(max_length=100, required=False)
    user_email = serializers.EmailField(required=False)
    user_phone = serializers.CharField(max_length=20, required=False)
    documents = serializers.ListField(child=serializers.DictField(), required=False)
    additional_data = serializers.DictField(required=False)
    source = serializers.CharField(max_length=100, default='web')


class KycSpecUpdateSerializer(serializers.Serializer):
    """Serializer for updating KYC dump status"""
    status = serializers.ChoiceField(
        choices=['collected', 'processed', 'contacted', 'converted'],
        required=False
    )
    notes = serializers.CharField(max_length=500, required=False)
    
    def validate(self, data):
        # Ensure at least one field is provided
        if not any(key in data for key in ['status', 'notes']):
            raise serializers.ValidationError(
                "At least one of 'status' or 'notes' must be provided"
            )
        return data