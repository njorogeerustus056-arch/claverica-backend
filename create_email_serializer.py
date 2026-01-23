import django
django.setup()

# SIMPLEJWT IMPORT PATCHED OUT
from rest_framework import exceptions
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT serializer that uses email instead of username"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field, add email field
        self.fields.pop('username', None)
        self.fields['email'] = self.fields.get('email', self.fields['password'].__class__())
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise exceptions.AuthenticationFailed(
                'Must include "email" and "password".',
                'missing_credentials'
            )
        
        # Authenticate using email
        user = authenticate(email=email, password=password)
        
        if user:
            if not user.is_active:
                raise exceptions.AuthenticationFailed(
                    'User account is disabled.',
                    'user_inactive'
                )
            
            # Get tokens
            refresh = self.get_token(user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            
            # Add user info
            data['user'] = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
            
            return data
        else:
            raise exceptions.AuthenticationFailed(
                'No active account found with the given credentials',
                'no_active_account'
            )

print("✅ EmailTokenObtainPairSerializer created successfully")
