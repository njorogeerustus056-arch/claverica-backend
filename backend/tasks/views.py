# tasks/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum, Q
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Task, UserTask, TaskCategory, RewardWithdrawal, UserRewardBalance
from .serializers import (
    TaskSerializer,
    UserTaskSerializer,
    UserTaskCreateSerializer,
    UserTaskSubmitSerializer,
    TaskCategorySerializer,
    RewardWithdrawalSerializer,
    RewardWithdrawalCreateSerializer,
    UserRewardBalanceSerializer,
)

User = get_user_model()


# --------------------------------------------------
# TASKS (READ-ONLY)
# --------------------------------------------------
class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        """Get available tasks excluding completed ones"""
        queryset = Task.objects.filter(status="active")
        
        # Exclude expired tasks
        queryset = queryset.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
        
        # Filter by type if provided
        task_type = self.request.query_params.get("type")
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        
        # Filter by availability
        availability = self.request.query_params.get("available", "").lower()
        if availability == "true":
            # Exclude tasks user has already started/completed
            completed_task_ids = UserTask.objects.filter(
                user=self.request.user
            ).values_list("task_id", flat=True)
            queryset = queryset.exclude(id__in=completed_task_ids)
        
        return queryset

    @action(detail=False, methods=["get"])
    def available(self, request):
        """Get tasks available to the current user"""
        # Get tasks user hasn't started/completed
        completed_task_ids = UserTask.objects.filter(
            user=request.user
        ).values_list("task_id", flat=True)
        
        tasks = self.get_queryset().exclude(id__in=completed_task_ids)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get task statistics"""
        active_tasks = Task.objects.filter(status="active")
        total_tasks = active_tasks.count()
        
        # Calculate available reward pool
        total_reward_pool = active_tasks.aggregate(
            total=Sum("reward_amount")
        ).get("total") or 0
        
        return Response(
            {
                "total_active_tasks": total_tasks,
                "total_reward_pool": float(total_reward_pool),
                "currency": "USD",
            }
        )


# --------------------------------------------------
# USER TASKS
# --------------------------------------------------
class UserTaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        """Get user tasks for the current user"""
        return UserTask.objects.filter(user=self.request.user).select_related('task')

    def get_serializer_class(self):
        """Use appropriate serializer based on action"""
        if self.action == "create":
            return UserTaskCreateSerializer
        elif self.action == "submit":
            return UserTaskSubmitSerializer
        return UserTaskSerializer

    def perform_create(self, serializer):
        """Create a new user task"""
        # The serializer validates and creates the UserTask
        # Signals will handle the balance updates
        user_task = serializer.save(
            user=self.request.user,
            status="in_progress",
            started_at=timezone.now()
        )
        return user_task

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Submit a task for review"""
        user_task = self.get_object()

        # Check if task can be submitted
        if user_task.status not in ["in_progress", "pending"]:
            return Response(
                {"detail": "This task cannot be submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserTaskSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update task with submission data
        user_task.submission_data = serializer.validated_data.get("submission_data", {})
        user_task.submission_notes = serializer.validated_data.get("submission_notes", "")
        user_task.status = "submitted"
        user_task.submitted_at = timezone.now()
        user_task.save()

        return Response(
            {
                "status": "success",
                "message": "Task submitted successfully.",
                "task": UserTaskSerializer(user_task).data,
            }
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Manually mark a task as completed (admin/reviewer action)"""
        user_task = self.get_object()

        if user_task.status == "completed":
            return Response(
                {"detail": "Task already completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark as completed - this will trigger signals
        user_task.mark_completed()
        
        # Refresh from database to get updated data
        user_task.refresh_from_db()

        return Response(
            {
                "status": "success",
                "message": "Task marked as completed.",
                "reward_earned": float(user_task.reward_earned),
                "task": UserTaskSerializer(user_task).data,
            }
        )

    @action(detail=False, methods=["get"])
    def completed(self, request):
        """Get completed tasks"""
        tasks = self.get_queryset().filter(status="completed")
        return Response(UserTaskSerializer(tasks, many=True).data)

    @action(detail=False, methods=["get"])
    def pending(self, request):
        """Get pending tasks (in progress or submitted)"""
        tasks = self.get_queryset().filter(
            status__in=["pending", "in_progress", "submitted", "under_review"]
        )
        return Response(UserTaskSerializer(tasks, many=True).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get user task statistics"""
        qs = self.get_queryset()

        total = qs.count()
        completed = qs.filter(status="completed").count()
        pending = qs.filter(
            status__in=["pending", "in_progress", "submitted", "under_review"]
        ).count()
        rejected = qs.filter(status="rejected").count()

        # Calculate total earned
        earned_result = qs.filter(status="completed").aggregate(
            total=Sum("reward_earned")
        )
        earned = earned_result.get("total") or 0

        return Response(
            {
                "total_tasks": total,
                "completed": completed,
                "pending": pending,
                "rejected": rejected,
                "total_earned": float(earned),
                "completion_rate": round((completed / total * 100), 2) if total > 0 else 0,
            }
        )


# --------------------------------------------------
# WITHDRAWALS
# --------------------------------------------------
class RewardWithdrawalViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch']

    def get_queryset(self):
        """Get withdrawals for the current user"""
        return RewardWithdrawal.objects.filter(user=self.request.user).order_by('-requested_at')

    def get_serializer_class(self):
        """Use appropriate serializer based on action"""
        if self.action == "create":
            return RewardWithdrawalCreateSerializer
        return RewardWithdrawalSerializer

    def perform_create(self, serializer):
        """Create a new withdrawal"""
        # The serializer validates the amount and creates the withdrawal
        withdrawal = serializer.save(
            user=self.request.user,
            status="pending",
            requested_at=timezone.now()
        )
        
        # Manually trigger the signal logic to avoid recursion
        balance = UserRewardBalance.objects.get(user=self.request.user)
        success = balance.deduct_withdrawal(withdrawal.amount)
        
        if not success:
            withdrawal.status = 'failed'
            withdrawal.processor_notes = 'Insufficient balance'
            withdrawal.save()
        else:
            withdrawal.transaction_id = f"WDR-{withdrawal.id:06d}"
            withdrawal.save()
        
        return withdrawal

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a pending withdrawal"""
        withdrawal = self.get_object()

        if withdrawal.status != "pending":
            return Response(
                {"detail": "Only pending withdrawals can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Refund the amount to balance
            balance = UserRewardBalance.objects.get(user=request.user)
            balance.available_balance += withdrawal.amount
            balance.total_withdrawn -= withdrawal.amount
            balance.save()

            # Mark withdrawal as cancelled
            withdrawal.status = "cancelled"
            withdrawal.processor_notes = "Cancelled by user"
            withdrawal.save()

        return Response(
            {
                "status": "success",
                "message": "Withdrawal cancelled successfully.",
                "refunded_amount": float(withdrawal.amount)
            }
        )


# --------------------------------------------------
# USER BALANCE
# --------------------------------------------------
class UserRewardBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserRewardBalanceSerializer

    def get_queryset(self):
        """Get balance for the current user"""
        return UserRewardBalance.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def my_balance(self, request):
        """Get current user's balance"""
        balance, _ = UserRewardBalance.objects.get_or_create(user=request.user)
        return Response(self.get_serializer(balance).data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get balance summary with recent activity"""
        balance, _ = UserRewardBalance.objects.get_or_create(user=request.user)

        # Get recent earnings (last 5 completed tasks)
        recent_earnings = UserTask.objects.filter(
            user=request.user,
            status="completed",
        ).select_related('task').order_by("-completed_at")[:5]

        # Get pending withdrawals
        pending_withdrawals = RewardWithdrawal.objects.filter(
            user=request.user,
            status__in=["pending", "processing"],
        ).order_by("-requested_at")

        return Response(
            {
                "balance": UserRewardBalanceSerializer(balance).data,
                "recent_earnings": UserTaskSerializer(recent_earnings, many=True).data,
                "pending_withdrawals": RewardWithdrawalSerializer(pending_withdrawals, many=True).data,
            }
        )


# --------------------------------------------------
# TASK CATEGORIES
# --------------------------------------------------
class TaskCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskCategorySerializer
    queryset = TaskCategory.objects.filter(is_active=True).order_by('display_order', 'name')