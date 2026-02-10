from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import Account
from .models import UserProfile, UserSettings
from transactions.models import Wallet

@receiver(post_save, sender=Account)
def create_user_profile_settings_and_wallet(sender, instance, created, **kwargs):
    """
    Automatically create UserProfile, UserSettings, and Wallet when Account is created.
    """
    if created:
        try:
            print(f'\n[USER SIGNAL] Creating components for {instance.email}')
            print(f'   Account#: {instance.account_number}')

            # Generate account number if not exists (for foreign key consistency)
            if not instance.account_number:
                # Generate account number even for unverified users
                from accounts.models import Account as AccModel
                instance.account_number = AccModel.objects.generate_account_number(instance)
                instance.save(update_fields=['account_number'])
                print(f'   ⚠️  Generated Account#: {instance.account_number}')

            # 1. Create UserProfile
            profile, p_created = UserProfile.objects.get_or_create(account=instance)
            if p_created:
                print(f'   ? Created UserProfile: {profile.id}')
            else:
                print(f'   ??  UserProfile exists: {profile.id}')

            # 2. Create UserSettings
            settings, s_created = UserSettings.objects.get_or_create(account=instance)
            if s_created:
                print(f'   ? Created UserSettings: {settings.id}')
            else:
                print(f'   ??  UserSettings exists: {settings.id}')

            # 3. Create Wallet
            wallet, w_created = Wallet.objects.get_or_create(
                account=instance,
                defaults={'balance': 0.00, 'currency': 'USD'}
            )
            if w_created:
                print(f'   ?? Created Wallet: {wallet.id}')
                print(f'   ?? Balance: {wallet.balance} {wallet.currency}')
            else:
                print(f'   ??  Wallet exists: {wallet.id}')

            print('   ? All components created!')

        except Exception as e:
            print(f'   ? Error: {e}')
            import traceback
            traceback.print_exc()
