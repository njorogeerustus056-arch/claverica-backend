from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskCategoryViewSet, ClavericaTaskViewSet

router = DefaultRouter()
router.register(r'categories', TaskCategoryViewSet, basename='taskcategory')
router.register(r'tasks', ClavericaTaskViewSet, basename='clavericatask')

urlpatterns = [
    path('', include(router.urls)),
]
