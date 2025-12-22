from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum

from .models import (
    Task,
    UserTask,
    TaskCategory,
    RewardWithdrawal,
    UserRewardBalance,
)
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


# --------------------------------------------------
# TASKS (READ-ONLY)
# --------------------------------------------------
class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = Task.objects.filter(status="active")

        task_type = self.request.query_params.get("type")
        if task_type:
            queryset = queryset.filter(task_type=task_type)

        return queryset

    @action(detail=False, methods=["get"])
    def available(self, request):
        completed_task_ids = UserTask.objects.filter(
            user=request.user
        ).values_list("task_id", flat=True)

        tasks = self.get_queryset().exclude(id__in=completed_task_ids)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        total_tasks = Task.objects.filter(status="active").count()
        total_reward_pool = (
            Task.objects.filter(status="active")
            .aggregate(total=Sum("reward_amount"))
            .get("total")
            or 0
        )

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

    def get_queryset(self):
        return UserTask.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return UserTaskCreateSerializer
        return UserTaskSerializer

    def perform_create(self, serializer):
        user_task = serializer.save(
            user=self.request.user,
            status="in_progress",
        )

        balance, _ = UserRewardBalance.objects.get_or_create(
            user=self.request.user
        )
        balance.tasks_pending += 1
        balance.pending_balance += user_task.task.reward_amount
        balance.save()

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        user_task = self.get_object()

        if user_task.status not in ["in_progress", "pending"]:
            return Response(
                {"detail": "This task cannot be submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserTaskSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_task.submission_data = serializer.validated_data.get(
            "submission_data", {}
        )
        user_task.submission_notes = serializer.validated_data.get(
            "submission_notes", ""
        )
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
        user_task = self.get_object()

        if user_task.status == "completed":
            return Response(
                {"detail": "Task already completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_task.mark_completed()

        balance = UserRewardBalance.objects.get(user=user_task.user)
        balance.add_earnings(user_task.reward_earned)
        balance.tasks_pending = max(balance.tasks_pending - 1, 0)
        balance.pending_balance = max(
            balance.pending_balance - user_task.reward_earned, 0
        )
        balance.save()

        return Response(
            {
                "status": "success",
                "reward_earned": float(user_task.reward_earned),
                "task": UserTaskSerializer(user_task).data,
            }
        )

    @action(detail=False, methods=["get"])
    def completed(self, request):
        tasks = self.get_queryset().filter(status="completed")
        return Response(UserTaskSerializer(tasks, many=True).data)

    @action(detail=False, methods=["get"])
    def pending(self, request):
        tasks = self.get_queryset().filter(
            status__in=["pending", "in_progress", "submitted"]
        )
        return Response(UserTaskSerializer(tasks, many=True).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.get_queryset()

        total = qs.count()
        completed = qs.filter(status="completed").count()
        pending = qs.filter(
            status__in=["pending", "in_progress", "submitted"]
        ).count()
        rejected = qs.filter(status="rejected").count()

        earned = (
            qs.filter(status="completed")
            .aggregate(total=Sum("reward_earned"))
            .get("total")
            or 0
        )

        return Response(
            {
                "total_tasks": total,
                "completed": completed,
                "pending": pending,
                "rejected": rejected,
                "total_earned": float(earned),
                "completion_rate": round(
                    (completed / total * 100), 2
                )
                if total > 0
                else 0,
            }
        )


# --------------------------------------------------
# WITHDRAWALS
# --------------------------------------------------
class RewardWithdrawalViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RewardWithdrawal.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return RewardWithdrawalCreateSerializer
        return RewardWithdrawalSerializer

    def perform_create(self, serializer):
        withdrawal = serializer.save(user=self.request.user)
        balance = UserRewardBalance.objects.get(user=self.request.user)
        balance.deduct_withdrawal(withdrawal.amount)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        withdrawal = self.get_object()

        if withdrawal.status != "pending":
            return Response(
                {"detail": "Only pending withdrawals can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        balance = UserRewardBalance.objects.get(user=request.user)
        balance.available_balance += withdrawal.amount
        balance.total_withdrawn -= withdrawal.amount
        balance.save()

        withdrawal.status = "cancelled"
        withdrawal.save()

        return Response({"status": "success"})


# --------------------------------------------------
# USER BALANCE
# --------------------------------------------------
class UserRewardBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserRewardBalanceSerializer

    def get_queryset(self):
        return UserRewardBalance.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def my_balance(self, request):
        balance, _ = UserRewardBalance.objects.get_or_create(
            user=request.user
        )
        return Response(self.get_serializer(balance).data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        balance, _ = UserRewardBalance.objects.get_or_create(
            user=request.user
        )

        recent = UserTask.objects.filter(
            user=request.user,
            status="completed",
        ).order_by("-completed_at")[:5]

        pending_withdrawals = RewardWithdrawal.objects.filter(
            user=request.user,
            status__in=["pending", "processing"],
        )

        return Response(
            {
                "balance": UserRewardBalanceSerializer(balance).data,
                "recent_earnings": UserTaskSerializer(
                    recent, many=True
                ).data,
                "pending_withdrawals": RewardWithdrawalSerializer(
                    pending_withdrawals, many=True
                ).data,
            }
        )


# --------------------------------------------------
# TASK CATEGORIES
# --------------------------------------------------
class TaskCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskCategorySerializer
    queryset = TaskCategory.objects.filter(is_active=True)
