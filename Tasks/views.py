from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Count, Q

from .models import Task, UserTask, TaskCategory, RewardWithdrawal, UserRewardBalance
from .serializers import (
    TaskSerializer, UserTaskSerializer, UserTaskCreateSerializer,
    UserTaskSubmitSerializer, TaskCategorySerializer,
    RewardWithdrawalSerializer, RewardWithdrawalCreateSerializer,
    UserRewardBalanceSerializer
)


class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing available tasks
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer
    
    def get_queryset(self):
        queryset = Task.objects.filter(status='active')
        
        # Filter by type
        task_type = self.request.query_params.get('type', None)
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get all available tasks for the current user"""
        # Tasks not yet started or completed by user
        completed_task_ids = UserTask.objects.filter(
            user=request.user
        ).values_list('task_id', flat=True)
        
        available_tasks = self.get_queryset().exclude(
            id__in=completed_task_ids
        )
        
        serializer = self.get_serializer(available_tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get task statistics"""
        total_tasks = Task.objects.filter(status='active').count()
        total_reward_pool = Task.objects.filter(status='active').aggregate(
            total=Sum('reward_amount')
        )['total'] or 0
        
        return Response({
            'total_active_tasks': total_tasks,
            'total_reward_pool': float(total_reward_pool),
            'currency': 'USD'
        })


class UserTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user task completions
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserTask.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserTaskCreateSerializer
        return UserTaskSerializer
    
    def perform_create(self, serializer):
        # Start a new task
        user_task = serializer.save(user=self.request.user, status='in_progress')
        
        # Create or update user reward balance
        balance, created = UserRewardBalance.objects.get_or_create(user=self.request.user)
        balance.tasks_pending += 1
        balance.pending_balance += user_task.task.reward_amount
        balance.save()
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit a completed task"""
        user_task = self.get_object()
        
        if user_task.status not in ['in_progress', 'pending']:
            return Response({
                'status': 'error',
                'message': 'This task cannot be submitted'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserTaskSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Update task
        user_task.submission_data = serializer.validated_data.get('submission_data', {})
        user_task.submission_notes = serializer.validated_data.get('submission_notes', '')
        user_task.status = 'submitted'
        user_task.submitted_at = timezone.now()
        user_task.save()
        
        return Response({
            'status': 'success',
            'message': 'Task submitted successfully',
            'task': UserTaskSerializer(user_task).data
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark task as completed and award reward (admin/auto-complete)"""
        user_task = self.get_object()
        
        if user_task.status == 'completed':
            return Response({
                'status': 'error',
                'message': 'Task already completed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark as completed
        user_task.mark_completed()
        
        # Update user balance
        balance = UserRewardBalance.objects.get(user=user_task.user)
        balance.add_earnings(user_task.reward_earned)
        balance.tasks_pending -= 1
        balance.pending_balance -= user_task.reward_earned
        balance.save()
        
        return Response({
            'status': 'success',
            'message': 'Task completed and reward awarded',
            'reward_earned': float(user_task.reward_earned),
            'task': UserTaskSerializer(user_task).data
        })
    
    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get all completed tasks"""
        completed_tasks = self.get_queryset().filter(status='completed')
        serializer = self.get_serializer(completed_tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending/in-progress tasks"""
        pending_tasks = self.get_queryset().filter(
            status__in=['pending', 'in_progress', 'submitted']
        )
        serializer = self.get_serializer(pending_tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user task statistics"""
        queryset = self.get_queryset()
        
        total_tasks = queryset.count()
        completed = queryset.filter(status='completed').count()
        pending = queryset.filter(status__in=['pending', 'in_progress', 'submitted']).count()
        rejected = queryset.filter(status='rejected').count()
        
        total_earned = queryset.filter(status='completed').aggregate(
            total=Sum('reward_earned')
        )['total'] or 0
        
        return Response({
            'total_tasks': total_tasks,
            'completed': completed,
            'pending': pending,
            'rejected': rejected,
            'total_earned': float(total_earned),
            'completion_rate': round((completed / total_tasks * 100), 2) if total_tasks > 0 else 0
        })


class RewardWithdrawalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reward withdrawals
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return RewardWithdrawal.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RewardWithdrawalCreateSerializer
        return RewardWithdrawalSerializer
    
    def perform_create(self, serializer):
        withdrawal = serializer.save(user=self.request.user)
        
        # Deduct from available balance
        balance = UserRewardBalance.objects.get(user=self.request.user)
        balance.deduct_withdrawal(withdrawal.amount)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending withdrawal"""
        withdrawal = self.get_object()
        
        if withdrawal.status != 'pending':
            return Response({
                'status': 'error',
                'message': 'Only pending withdrawals can be cancelled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Return amount to balance
        balance = UserRewardBalance.objects.get(user=request.user)
        balance.available_balance += withdrawal.amount
        balance.total_withdrawn -= withdrawal.amount
        balance.save()
        
        # Update withdrawal status
        withdrawal.status = 'cancelled'
        withdrawal.save()
        
        return Response({
            'status': 'success',
            'message': 'Withdrawal cancelled successfully'
        })


class UserRewardBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user reward balance
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserRewardBalanceSerializer
    
    def get_queryset(self):
        return UserRewardBalance.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_balance(self, request):
        """Get current user's reward balance"""
        balance, created = UserRewardBalance.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(balance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get balance summary with breakdown"""
        balance, created = UserRewardBalance.objects.get_or_create(user=request.user)
        
        # Get recent earnings
        recent_earnings = UserTask.objects.filter(
            user=request.user,
            status='completed'
        ).order_by('-completed_at')[:5]
        
        # Get pending withdrawals
        pending_withdrawals = RewardWithdrawal.objects.filter(
            user=request.user,
            status__in=['pending', 'processing']
        )
        
        return Response({
            'balance': UserRewardBalanceSerializer(balance).data,
            'recent_earnings': UserTaskSerializer(recent_earnings, many=True).data,
            'pending_withdrawals': RewardWithdrawalSerializer(pending_withdrawals, many=True).data
        })


class TaskCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing task categories
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskCategorySerializer
    queryset = TaskCategory.objects.filter(is_active=True)
