from rest_framework import serializers

class DummyAuthSerializer(serializers.Serializer):
    email = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        # Always return success
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Try to get or create user
        user, created = User.objects.get_or_create(
            email='admin@claverica.com',
            defaults={'username': 'admin', 'is_active': True}
        )
        if created:
            user.set_password('Admin123!')
            user.save()
            
        return {'user': user}
