from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecipientViewSet, TransferViewSet
from . import views  # ADD THIS IMPORT

router = DefaultRouter()
router.register(r'recipients', RecipientViewSet, basename='recipient')
router.register(r'transfers', TransferViewSet, basename='transfer')

urlpatterns = [
    path('', include(router.urls)),
]