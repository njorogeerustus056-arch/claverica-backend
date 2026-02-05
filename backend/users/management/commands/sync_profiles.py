from django.core.management.base import BaseCommand
from accounts.models import Account
from users.models import UserProfile, UserSettings

class Command(BaseCommand):
    help = "Create missing UserProfile and UserSettings for existing Accounts"
    
    def handle(self, *args, **options):
        accounts = Account.objects.all()
        self.stdout.write(f"Checking {accounts.count()} accounts...")
        
        profiles_created = 0
        settings_created = 0
        
        for account in accounts:
            # Create UserProfile if missing
            try:
                profile = account.user_profile
                self.stdout.write(f"  {account.email}: Profile exists")
            except:
                profile = UserProfile.objects.create(account=account)
                profiles_created += 1
                self.stdout.write(f"  {account.email}: Created profile")
            
            # Create UserSettings if missing
            try:
                settings = account.user_settings
                self.stdout.write(f"  {account.email}: Settings exist")
            except:
                settings = UserSettings.objects.create(account=account)
                settings_created += 1
                self.stdout.write(f"  {account.email}: Created settings")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Success! Created {profiles_created} profiles and {settings_created} settings"
            )
        )
