# Tasks/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Task, UserTask, UserRewardBalance, RewardWithdrawal, TaskCategory
from django.utils import timezone
from datetime import timedelta
import json

User = get_user_model()

# -------------------------
# Task Model Tests
# -------------------------
class TaskModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            password='12345'
        )
        # UserRewardBalance will be created automatically by signal
    
    def test_create_task(self):
        task = Task.objects.create(
            title='Test Product Review',
            description='Review our new product',
            task_type='review',
            reward_amount=Decimal('25.00'),
            estimated_time=10
        )
        self.assertEqual(task.task_type, 'review')
        self.assertTrue(task.is_available())
    
    def test_task_availability(self):
        task = Task.objects.create(
            title='Limited Task',
            description='Limited availability task',
            task_type='review',
            reward_amount=Decimal('50.00'),
            max_completions=2,
            current_completions=0
        )
        self.assertTrue(task.is_available())
        
        # Simulate completions
        task.current_completions = 2
        task.save()
        self.assertFalse(task.is_available())
    
    def test_task_expired(self):
        task = Task.objects.create(
            title='Expired Task',
            description='This task has expired',
            task_type='review',
            reward_amount=Decimal('30.00'),
            expires_at=timezone.now() - timedelta(days=1),
            status='active'
        )
        self.assertFalse(task.is_available())
    
    def test_task_inactive(self):
        task = Task.objects.create(
            title='Inactive Task',
            description='This task is inactive',
            task_type='survey',
            reward_amount=Decimal('20.00'),
            status='inactive'
        )
        self.assertFalse(task.is_available())
    
    def test_task_str_method(self):
        task = Task.objects.create(
            title='Test Task',
            description='Test description',
            task_type='review',
            reward_amount=Decimal('25.00')
        )
        expected_str = f'Test Task - 25.00 USD'
        self.assertEqual(str(task), expected_str)

# -------------------------
# UserTask Model Tests
# -------------------------
class UserTaskModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            password='12345'
        )
        self.task = Task.objects.create(
            title='Test Task',
            description='Test description',
            task_type='review',
            reward_amount=Decimal('30.00')
        )
        # UserRewardBalance will be created automatically by signal
    
    def test_start_task(self):
        # Get or create balance (signal should have created it)
        balance, created = UserRewardBalance.objects.get_or_create(user=self.user)
        
        user_task = UserTask.objects.create(
            user=self.user,
            task=self.task,
            status='in_progress'
        )
        self.assertEqual(user_task.status, 'in_progress')
    
    def test_complete_task(self):
        # Get or create balance (signal should have created it)
        balance, created = UserRewardBalance.objects.get_or_create(user=self.user)
        
        user_task = UserTask.objects.create(
            user=self.user,
            task=self.task,
            status='submitted'
        )
        initial_completions = self.task.current_completions
        user_task.mark_completed()
        
        self.assertEqual(user_task.status, 'completed')
        self.assertEqual(user_task.reward_earned, Decimal('30.00'))
        self.assertIsNotNone(user_task.completed_at)
        self.assertEqual(self.task.current_completions, initial_completions + 1)
    
    def test_user_task_unique_constraint(self):
        UserTask.objects.create(
            user=self.user,
            task=self.task,
            status='in_progress'
        )
        
        # Should raise integrity error on duplicate
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            UserTask.objects.create(
                user=self.user,
                task=self.task,
                status='pending'
            )
    
    def test_user_task_submission_data(self):
        user_task = UserTask.objects.create(
            user=self.user,
            task=self.task,
            status='in_progress'
        )
        
        submission_data = {
            'rating': 5,
            'comment': 'Excellent product!',
            'images': ['img1.jpg']
        }
        
        user_task.submission_data = submission_data
        user_task.submission_notes = 'Submitted via web'
        user_task.save()
        
        user_task.refresh_from_db()
        self.assertEqual(user_task.submission_data['rating'], 5)
        self.assertEqual(user_task.submission_notes, 'Submitted via web')
    
    def test_user_task_str_method(self):
        user_task = UserTask.objects.create(
            user=self.user,
            task=self.task,
            status='in_progress'
        )
        expected_str = f'{self.user.email} - {self.task.title} - in_progress'
        self.assertEqual(str(user_task), expected_str)

# -------------------------
# UserRewardBalance Tests
# -------------------------
class UserRewardBalanceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            password='12345'
        )
        # Get the balance created by signal
        self.balance = UserRewardBalance.objects.get(user=self.user)
    
    def test_add_earnings(self):
        initial_balance = self.balance.available_balance
        initial_earned = self.balance.total_earned
        initial_tasks = self.balance.tasks_completed
        
        self.balance.add_earnings(Decimal('50.00'))
        
        self.assertEqual(
            self.balance.available_balance,
            initial_balance + Decimal('50.00')
        )
        self.assertEqual(
            self.balance.total_earned,
            initial_earned + Decimal('50.00')
        )
        self.assertEqual(self.balance.tasks_completed, initial_tasks + 1)
    
    def test_deduct_withdrawal(self):
        self.balance.available_balance = Decimal('100.00')
        self.balance.total_withdrawn = Decimal('0.00')
        self.balance.save()
        
        success = self.balance.deduct_withdrawal(Decimal('50.00'))
        
        self.assertTrue(success)
        self.assertEqual(self.balance.available_balance, Decimal('50.00'))
        self.assertEqual(self.balance.total_withdrawn, Decimal('50.00'))
    
    def test_insufficient_balance_withdrawal(self):
        self.balance.available_balance = Decimal('20.00')
        self.balance.save()
        
        success = self.balance.deduct_withdrawal(Decimal('50.00'))
        
        self.assertFalse(success)
        self.assertEqual(self.balance.available_balance, Decimal('20.00'))
        self.assertEqual(self.balance.total_withdrawn, Decimal('0.00'))
    
    def test_balance_str_method(self):
        self.balance.available_balance = Decimal('150.75')
        self.balance.save()
        expected_str = f'{self.user.email} - Balance: 150.75 USD'
        self.assertEqual(str(self.balance), expected_str)

# -------------------------
# RewardWithdrawal Tests
# -------------------------
class RewardWithdrawalTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            password='12345'
        )
        # Get the balance created by signal
        self.balance = UserRewardBalance.objects.get(user=self.user)
        # Set sufficient balance for tests
        self.balance.available_balance = Decimal('200.00')
        self.balance.save()
    
    def test_create_withdrawal(self):
        withdrawal = RewardWithdrawal.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            withdrawal_method='paypal',
            account_details={'email': 'test@example.com'}
        )
        
        self.assertEqual(withdrawal.amount, Decimal('50.00'))
        self.assertEqual(withdrawal.withdrawal_method, 'paypal')
        # Status should be pending (not failed since we have sufficient balance)
        self.assertEqual(withdrawal.status, 'pending')
        self.assertEqual(withdrawal.account_details['email'], 'test@example.com')
    
    def test_withdrawal_str_method(self):
        withdrawal = RewardWithdrawal.objects.create(
            user=self.user,
            amount=Decimal('75.50'),
            withdrawal_method='bank',
            account_details={'account': '123456'}
        )
        expected_str = f'{self.user.email} - 75.50 USD - pending'
        self.assertEqual(str(withdrawal), expected_str)
    
    def test_withdrawal_bank_details(self):
        bank_details = {
            'bank_name': 'Test Bank',
            'account_number': '1234567890',
            'routing_number': '021000021',
            'account_type': 'checking'
        }
        
        withdrawal = RewardWithdrawal.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            withdrawal_method='bank',
            account_details=bank_details
        )
        
        withdrawal.refresh_from_db()
        self.assertEqual(withdrawal.account_details['bank_name'], 'Test Bank')
        self.assertEqual(withdrawal.account_details['account_number'], '1234567890')

# -------------------------
# TaskCategory Tests
# -------------------------
class TaskCategoryTest(TestCase):
    def setUp(self):
        self.category = TaskCategory.objects.create(
            name='Review Tasks',
            description='Tasks for product reviews',
            icon='📝',
            color='blue',
            is_active=True,
            display_order=1
        )
    
    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Review Tasks')
        self.assertEqual(self.category.icon, '📝')
        self.assertTrue(self.category.is_active)
    
    def test_category_str_method(self):
        self.assertEqual(str(self.category), 'Review Tasks')
    
    def test_category_ordering(self):
        # Create more categories
        category2 = TaskCategory.objects.create(
            name='Survey Tasks',
            description='Survey tasks',
            icon='📊',
            color='green',
            is_active=True,
            display_order=2
        )
        
        category3 = TaskCategory.objects.create(
            name='Verification Tasks',
            description='Account verification tasks',
            icon='✅',
            color='red',
            is_active=True,
            display_order=1  # Same order as first
        )
        
        categories = TaskCategory.objects.all()
        self.assertEqual(categories[0].name, 'Review Tasks')  # Same order, created first
        self.assertEqual(categories[1].name, 'Verification Tasks')  # Same order
        self.assertEqual(categories[2].name, 'Survey Tasks')  # Order 2

# -------------------------
# Integration Tests
# -------------------------
class IntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            password='12345'
        )
        self.task = Task.objects.create(
            title='Integration Test Task',
            description='Task for integration testing',
            task_type='review',
            reward_amount=Decimal('40.00'),
            status='active'
        )
        # Get balance created by signal
        self.balance = UserRewardBalance.objects.get(user=self.user)
    
    def test_complete_task_workflow(self):
        """Test the complete workflow: start -> submit -> complete"""
        
        # 1. Start task
        user_task = UserTask.objects.create(
            user=self.user,
            task=self.task,
            status='in_progress'
        )
        self.assertEqual(user_task.status, 'in_progress')
        
        # Check pending balance was updated by signal
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.pending_balance, Decimal('40.00'))
        self.assertEqual(self.balance.tasks_pending, 1)
        
        # 2. Submit task
        user_task.submission_data = {'answer': 'Test submission'}
        user_task.submission_notes = 'Test notes'
        user_task.status = 'submitted'
        user_task.submitted_at = timezone.now()
        user_task.save()
        
        self.assertEqual(user_task.status, 'submitted')
        self.assertIsNotNone(user_task.submitted_at)
        
        # 3. Complete task
        user_task.mark_completed()
        user_task.status = 'completed'
        user_task.save()  # This triggers the signal
        
        self.assertEqual(user_task.status, 'completed')
        self.assertEqual(user_task.reward_earned, Decimal('40.00'))
        self.assertIsNotNone(user_task.completed_at)
        
        # 4. Check task completion count
        self.task.refresh_from_db()
        self.assertEqual(self.task.current_completions, 1)
        
        # 5. Check balance updated by signal
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.available_balance, Decimal('40.00'))
        self.assertEqual(self.balance.total_earned, Decimal('40.00'))
        self.assertEqual(self.balance.tasks_completed, 1)
        self.assertEqual(self.balance.pending_balance, Decimal('0.00'))
        self.assertEqual(self.balance.tasks_pending, 0)
    
    def test_withdrawal_workflow(self):
        """Test balance -> withdrawal workflow"""
        
        # Set initial balance
        self.balance.available_balance = Decimal('200.00')
        self.balance.save()
        
        # Create withdrawal
        withdrawal = RewardWithdrawal.objects.create(
            user=self.user,
            amount=Decimal('150.00'),
            withdrawal_method='paypal',
            account_details={'email': 'user@example.com'}
        )
        
        # Signal should have deducted the balance
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.available_balance, Decimal('50.00'))
        self.assertEqual(self.balance.total_withdrawn, Decimal('150.00'))
        
        # Check withdrawal status
        withdrawal.refresh_from_db()
        self.assertEqual(withdrawal.status, 'pending')
        
        # Simulate processing
        withdrawal.status = 'processing'
        withdrawal.processor_notes = 'Processing via PayPal'
        withdrawal.save()
        
        withdrawal.refresh_from_db()
        self.assertEqual(withdrawal.status, 'processing')
        self.assertEqual(withdrawal.processor_notes, 'Processing via PayPal')