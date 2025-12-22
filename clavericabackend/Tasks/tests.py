# Tasks/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Task, UserTask, UserRewardBalance

Account = get_user_model()  # Use custom Account model

# -------------------------
# Task Model Tests
# -------------------------
class TaskModelTest(TestCase):
    def setUp(self):
        self.user = Account.objects.create_user(
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            password='12345'
        )
    
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

# -------------------------
# UserTask Model Tests
# -------------------------
class UserTaskModelTest(TestCase):
    def setUp(self):
        self.user = Account.objects.create_user(
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
        UserRewardBalance.objects.create(user=self.user)
    
    def test_start_task(self):
        user_task = UserTask.objects.create(
            user=self.user,
            task=self.task,
            status='in_progress'
        )
        self.assertEqual(user_task.status, 'in_progress')
    
    def test_complete_task(self):
        user_task = UserTask.objects.create(
            user=self.user,
            task=self.task,
            status='submitted'
        )
        user_task.mark_completed()
        
        self.assertEqual(user_task.status, 'completed')
        self.assertEqual(user_task.reward_earned, Decimal('30.00'))
        self.assertIsNotNone(user_task.completed_at)

# -------------------------
# UserRewardBalance Tests
# -------------------------
class UserRewardBalanceTest(TestCase):
    def setUp(self):
        self.user = Account.objects.create_user(
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            password='12345'
        )
        self.balance = UserRewardBalance.objects.create(user=self.user)
    
    def test_add_earnings(self):
        initial_balance = self.balance.available_balance
        self.balance.add_earnings(Decimal('50.00'))
        
        self.assertEqual(
            self.balance.available_balance,
            initial_balance + Decimal('50.00')
        )
        self.assertEqual(self.balance.total_earned, Decimal('50.00'))
        self.assertEqual(self.balance.tasks_completed, 1)
    
    def test_deduct_withdrawal(self):
        self.balance.available_balance = Decimal('100.00')
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
