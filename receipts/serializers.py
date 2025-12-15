from rest_framework import serializers
from .models import Receipt

class ReceiptSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.ReadOnlyField()
    
    class Meta:
        model = Receipt
        fields = [
            'id', 'user_id', 'file_name', 'original_file_name', 
            'file_size', 'file_size_mb', 'file_type', 'storage_path',
            'merchant_name', 'amount', 'currency', 'transaction_date',
            'category', 'notes', 'tags', 'status', 
            'uploaded_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uploaded_at', 'updated_at', 'file_size_mb']


class ReceiptUploadSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=255)
    file = serializers.FileField()
    merchant_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    currency = serializers.CharField(max_length=3, default='USD')
    transaction_date = serializers.DateTimeField(required=False, allow_null=True)
    category = serializers.ChoiceField(choices=Receipt.CATEGORY_CHOICES, default='other')
    notes = serializers.CharField(required=False, allow_blank=True)
    tags = serializers.ListField(child=serializers.CharField(), required=False)


class ReceiptUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = [
            'merchant_name', 'amount', 'currency', 'transaction_date',
            'category', 'notes', 'tags', 'status'
        ]
