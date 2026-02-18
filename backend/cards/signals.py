# ========== FIXED: Use correct User model ==========
# @receiver(post_save, sender=USER_MODEL)
# def create_default_card(sender, instance, created, **kwargs):
#     """Create a default virtual card for new users - FIXED"""
#     if created:
#         try:
#             from .services import CardService
#             account = instance
#             if Card.objects.filter(account=account).exists():
#                 return
#             card = CardService.create_card(
#                 account=account,
#                 card_type='virtual',
#                 is_primary=True,
#                 cardholder_name=f'{account.first_name or ""} {account.last_name or ""}'.strip() or account.email,
#                 color_scheme='blue-gradient'
#             )
#             logger.info(f"Created default card for account {account.email}")
#         except Exception as e:
#             logger.error(f"Failed to create default card for account {instance.email}: {e}")
