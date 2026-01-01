from rest_framework import serializers
from .models import Receipt

class ReceiptSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Receipt
        fields = [
            'id', 'user', 'user_email', 'file', 'original_file_name', 
            'file_size', 'file_size_mb', 'file_type',
            'merchant_name', 'amount', 'currency', 'transaction_date',
            'category', 'notes', 'tags', 'status', 
            'uploaded_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_email', 'uploaded_at', 'updated_at', 
            'file_size_mb', 'original_file_name', 'file_size', 'file_type'
        ]

    def get_file_size_mb(self, obj):
        return obj.file_size_mb


class ReceiptUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = [
            'file', 'merchant_name', 'amount', 'currency', 
            'transaction_date', 'category', 'notes', 'tags'
        ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class ReceiptUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = [
            'merchant_name', 'amount', 'currency', 'transaction_date',
            'category', 'notes', 'tags', 'status'
        ]