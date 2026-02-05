# DISABLED - Users app now handles all signal processing
# This file is kept for reference but signals are disabled

# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Account
# from users.models import UserProfile, UserSettings
# from transactions.models import Wallet

# @receiver(post_save, sender=Account)
# def create_user_profile_settings_and_wallet(sender, instance, created, **kwargs):
#     """DISABLED - Users app handles this now"""
#     pass
