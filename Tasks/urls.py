from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet, UserTaskViewSet, RewardWithdrawalViewSet,
    UserRewardBalanceViewSet, TaskCategoryViewSet
)

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'user-tasks', UserTaskViewSet, basename='user-task')
router.register(r'withdrawals', RewardWithdrawalViewSet, basename='withdrawal')
router.register(r'balance', UserRewardBalanceViewSet, basename='balance')
router.register(r'categories', TaskCategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
]
