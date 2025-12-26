# accounts/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in with either:
    - Email address
    - Username (if your Account model has a username field)
    
    This backend is compatible with DRF Simple JWT which passes credentials
    as 'username' parameter regardless of what field you're actually using.
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
            # Try to fetch the user by searching for email OR username
            # Since your USERNAME_FIELD is 'email', we primarily look for email
            # But we also check username field if it exists on your model
            
            # If your Account model ONLY has email (no separate username field):
            user = UserModel.objects.get(email=username)
            
            # If your Account model HAS both email and username fields, use this instead:
            # user = UserModel.objects.get(
            #     Q(email=username) | Q(username=username)
            # )
            
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            # This shouldn't happen if email is unique, but handle it gracefully
            return None
        else:
            # Verify the password and check if user can authenticate
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        
        return None
    
    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False. Custom user models that don't have
        an `is_active` field are allowed.
        """
        return getattr(user, 'is_active', True)