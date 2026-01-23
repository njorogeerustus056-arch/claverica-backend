# accounts/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in with email.
    Simple JWT passes the login identifier as 'username' parameter.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        # Simple JWT passes the login identifier as 'username' parameter
        # We need to handle both 'username' and 'email' parameters
        if username is None:
            username = kwargs.get('email')
        
        if username is None or password is None:
            return None
        
        try:
            # Look for user by email
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce timing attack
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            return None
        else:
            # Verify the password and check if user can authenticate
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        
        return None