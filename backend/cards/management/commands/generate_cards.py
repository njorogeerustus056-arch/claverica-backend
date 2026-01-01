"""
cards/management/commands/generate_cards.py
Management command to generate test cards
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from cards.models import Card, CardStatus
from decimal import Decimal
import random
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate test cards for development'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of cards to generate'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created test user: {user.username}'))
        
        # Generate cards
        for i in range(count):
            card_number = ''.join([str(random.randint(0, 9)) for _ in range(16)])
            expiry_date = (datetime.now() + timedelta(days=1825)).strftime("%m/%y")
            
            card = Card.objects.create(
                user=user,
                card_type='virtual' if i % 2 == 0 else 'physical',
                card_number=card_number,
                last_four=card_number[-4:],
                cvv=''.join([str(random.randint(0, 9)) for _ in range(3)]),
                expiry_date=expiry_date,
                cardholder_name=f'{user.first_name} {user.last_name}',
                balance=Decimal(random.uniform(100, 5000)).quantize(Decimal('0.00')),
                spending_limit=Decimal('5000.00'),
                status=CardStatus.ACTIVE,
                is_primary=(i == 0),
                color_scheme='from-indigo-500 via-purple-500 to-pink-500'
            )
            
            self.stdout.write(self.style.SUCCESS(f'Created card: {card.last_four}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nGenerated {count} cards for {user.username}'))