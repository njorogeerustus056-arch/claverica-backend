from rest_framework import serializers
from .models import Receipt

class ReceiptSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = Receipt
        fields = [
            'id', 'user', 'file', 'original_file_name', 
            'file_size', 'file_size_mb', 'file_type',
            'merchant_name', 'amount', 'currency', 'transaction_date',
            'category', 'notes', 'tags', 'status', 
            'uploaded_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uploaded_at', 'updated_at', 'file_size_mb', 'original_file_name', 'file_size', 'file_type', 'user']

    def get_file_size_mb(self, obj):
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0.0


class ReceiptUploadSerializer(serializers.Serializer):
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
