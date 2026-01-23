from rest_framework import serializers

class DummySerializer(serializers.Serializer):
    email = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    
    def validate(self, attrs):
        # Always return valid
        return {"user": {"id": 1, "email": "admin@claverica.com"}}
