# payments/__init__.py
default_app_config = 'payments.apps.PaymentsConfig'

# Import signals to ensure they're registered
try:
    import payments.signals
except ImportError:
    pass