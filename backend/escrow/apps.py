from django.apps import AppConfig

class EscrowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.escrow'
    label = 'escrow_final'
