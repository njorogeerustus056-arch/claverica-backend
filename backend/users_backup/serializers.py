# users/serializers.py - CREATE THIS NEW FILE
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile creation/update"""
    
    class Meta:
        model = UserProfile
        fields = [
            'phone', 'document_type', 'document_number', 'street',
            'city', 'state', 'zip_code', 'occupation', 'employer',
            'income_range', 'avatar_color'
        ]
        extra_kwargs = {
            'phone': {'required': False, 'allow_blank': True},
            'document_type': {'required': False, 'allow_blank': True},
            'document_number': {'required': False, 'allow_blank': True},
            'street': {'required': False, 'allow_blank': True},
            'city': {'required': False, 'allow_blank': True},
            'state': {'required': False, 'allow_blank': True},
            'zip_code': {'required': False, 'allow_blank': True},
            'occupation': {'required': False, 'allow_blank': True},
            'employer': {'required': False, 'allow_blank': True},
            'income_range': {'required': False, 'allow_blank': True},
            'avatar_color': {'required': False, 'allow_blank': True},
        }
    
    def validate_phone(self, value):
        """Optional phone validation"""
        if value and len(value) < 10:
            raise serializers.ValidationError(_("Phone number too short"))
        return value
    
    def validate_zip_code(self, value):
        """Optional zip code validation"""
        if value and not value.isdigit():
            raise serializers.ValidationError(_("ZIP code must contain only digits"))
        return value