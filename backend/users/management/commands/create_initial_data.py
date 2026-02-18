# users/management/commands/create_initial_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import UserProfile, UserSettings, ActivityLog, ConnectedDevice
import uuid

class Command(BaseCommand):
    help = 'Create initial test data for users app'

    def handle(self, *args, **options):
        Account = get_user_model()
        
        # Create test users if they don't exist
        users_data = [
            {
                'email': 'test@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'password': 'password123',
                'phone': '+254712345678',
                'is_verified': True,
                'is_active': True,
            },
        ]
        
        for user_data in users_data:
            email = user_data['email']
            if not Account.objects.filter(email=email).exists():
                user = Account.objects.create_user(**user_data)
                self.stdout.write(f'Created user: {email}')
                
                # Create sample connected device
                ConnectedDevice.objects.create(
                    account=user,
                    device_id=str(uuid.uuid4()),
                    device_name='iPhone 13',
                    device_type='mobile',
                    is_current=True,
                    location='Nairobi, Kenya'
                )
                
                # Create sample activity log
                ActivityLog.objects.create(
                    account=user,
                    action='login',
                    description='User logged in successfully',
                    device='Chrome on macOS',
                    ip_address='192.168.1.100',
                    location='Nairobi, KE'
                )
                
                self.stdout.write(f'Created sample data for: {email}')
        
        self.stdout.write(self.style.SUCCESS('Initial data created successfully!'))
