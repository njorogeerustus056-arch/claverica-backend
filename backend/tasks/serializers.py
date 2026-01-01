from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Task, UserTask, TaskCategory, RewardWithdrawal, UserRewardBalance

User = get_user_model()


class TaskCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskCategory
        fields = ['id', 'name', 'description', 'icon', 'color', 'is_active', 'display_order']


class TaskSerializer(serializers.ModelSerializer):
    is_available = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'task_type', 'reward_amount', 'currency',
            'estimated_time', 'max_completions', 'current_completions',
            'requires_verification', 'min_account_age_days', 'status',
            'instructions', 'created_at', 'expires_at', 'is_available', 'completion_rate'
        ]
        read_only_fields = ['id', 'current_completions', 'created_at']
    
    def get_is_available(self, obj):
        return obj.is_available()
    
    def get_completion_rate(self, obj):
        if obj.max_completions and obj.max_completions > 0:
            return round((obj.current_completions / obj.max_completions) * 100, 2)
        return 0


class UserTaskSerializer(serializers.ModelSerializer):
    task_details = TaskSerializer(source='task', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserTask
        fields = [
            'id', 'user', 'username', 'task', 'task_details', 'status',
            'submission_data', 'submission_notes', 'reward_earned',
            'reward_paid', 'reward_paid_at', 'started_at',
            'submitted_at', 'completed_at', 'review_notes'
        ]
        read_only_fields = [
            'id', 'user', 'reward_earned', 'reward_paid',
            'reward_paid_at', 'started_at', 'completed_at'
        ]


class UserTaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTask
        fields = ['task']
    
    def validate_task(self, value):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is missing")
        
        user = request.user
        
        # Check if user already started/completed this task
        if UserTask.objects.filter(user=user, task=value).exists():
            raise serializers.ValidationError("You have already started or completed this task.")
        
        # Check if task is available
        if not value.is_available():
            raise serializers.ValidationError("This task is no longer available.")
        
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is missing")
        
        return UserTask.objects.create(
            user=request.user,
            task=validated_data['task'],
            status='in_progress'
        )


class UserTaskSubmitSerializer(serializers.Serializer):
    submission_data = serializers.JSONField(required=False)
    submission_notes = serializers.CharField(required=False, allow_blank=True)


class RewardWithdrawalSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = RewardWithdrawal
        fields = [
            'id', 'user', 'username', 'amount', 'currency',
            'withdrawal_method', 'account_details', 'status',
            'transaction_id', 'processor_notes', 'requested_at', 
            'processed_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'transaction_id', 'processor_notes',
            'requested_at', 'processed_at', 'completed_at'
        ]


class RewardWithdrawalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardWithdrawal
        fields = ['amount', 'withdrawal_method', 'account_details']
    
    def validate_amount(self, value):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is missing")
        
        user = request.user
        
        try:
            balance = UserRewardBalance.objects.get(user=user)
            if value > balance.available_balance:
                raise serializers.ValidationError(
                    f"Insufficient balance. Available: {balance.available_balance} {balance.currency}"
                )
        except UserRewardBalance.DoesNotExist:
            raise serializers.ValidationError("No reward balance found.")
        
        # Minimum withdrawal amount
        if value < 10:
            raise serializers.ValidationError("Minimum withdrawal amount is $10.")
        
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is missing")
        
        return RewardWithdrawal.objects.create(
            user=request.user,
            amount=validated_data['amount'],
            withdrawal_method=validated_data['withdrawal_method'],
            account_details=validated_data['account_details']
        )


class UserRewardBalanceSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserRewardBalance
        fields = [
            'id', 'user', 'username', 'total_earned', 'total_withdrawn',
            'available_balance', 'pending_balance', 'currency',
            'tasks_completed', 'tasks_pending', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']