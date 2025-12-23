# payments/tests.py
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from decimal import Decimal
from accounts.models import Account
from .models import Transaction, Card, Beneficiary, SavingsGoal, Subscription

class PaymentTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create a test user and account
        self.account_user = Account.objects.create_user(
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            password="Test1234!",
            phone="+1234567890",
            document_type="passport",
            document_number="A98765432",
            street="456 Park Ave",
            city="New York",
            state="NY",
            zip_code="10022",
            occupation="Engineer",
            employer="TechCorp",
            income_range="50k-100k"
        )

        # Authenticate client
        response = self.client.post(
            reverse('token_obtain_pair'),  # or your JWT login endpoint
            {'email': 'alice@example.com', 'password': 'Test1234!'},
            format='json'
        )
        self.access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        # Create a second account for transfers
        self.recipient_user = Account.objects.create_user(
            first_name="Bob",
            last_name="Johnson",
            email="bob@example.com",
            password="Test1234!",
            phone="+1987654321",
            document_type="passport",
            document_number="B12345678",
            street="789 Broadway",
            city="New York",
            state="NY",
            zip_code="10003",
            occupation="Designer",
            employer="DesignCo",
            income_range="50k-100k"
        )

    def test_create_transaction(self):
        """Test creating a transaction"""
        payload = {
            "account_id": self.account_user.id,
            "amount": "100.00",
            "transaction_type": "payment",
            "currency": "USD",
            "description": "Test payment"
        }
        url = reverse('transaction-list')  # adjust to your router name
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.amount, Decimal("100.00"))
        self.assertEqual(transaction.account, self.account_user)

    def test_quick_transfer(self):
        """Test transferring funds to another account"""
        payload = {
            "recipient_account_number": self.recipient_user.account_number,
            "amount": "50.00",
            "currency": "USD",
            "description": "Quick transfer test"
        }
        url = reverse('quick_transfer')  # adjust to your endpoint
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.account_user.refresh_from_db()
        self.recipient_user.refresh_from_db()
        self.assertEqual(self.account_user.balance, Decimal("-50.00"))
        self.assertEqual(self.recipient_user.balance, Decimal("50.00"))

    def test_card_block_activate(self):
        """Test blocking and activating a card"""
        card = Card.objects.create(
            account=self.account_user,
            card_type="debit",
            cardholder_name="Alice Smith",
            card_number="1111222233334444",
            cvv="123",
            expiry_month=12,
            expiry_year=2030,
            status="active",
        )

        # Block card
        url = reverse('card-block', args=[card.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        card.refresh_from_db()
        self.assertEqual(card.status, "blocked")

        # Activate card
        url = reverse('card-activate', args=[card.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        card.refresh_from_db()
        self.assertEqual(card.status, "active")

    def test_savings_goal_deposit_withdraw(self):
        """Test depositing and withdrawing from a savings goal"""
        goal = SavingsGoal.objects.create(
            account=self.account_user,
            name="Emergency Fund",
            target_amount=Decimal("500.00"),
            current_amount=Decimal("0.00"),
            currency="USD",
            status="active"
        )

        # Deposit
        deposit_url = reverse('savingsgoal-deposit', args=[goal.id])
        response = self.client.post(deposit_url, {"amount": "100.00"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.current_amount, Decimal("100.00"))

        # Withdraw
        withdraw_url = reverse('savingsgoal-withdraw', args=[goal.id])
        response = self.client.post(withdraw_url, {"amount": "50.00"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.current_amount, Decimal("50.00"))
