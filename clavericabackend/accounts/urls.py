# accounts/urls.py
from django.urls import path
from .views import index, RegisterView

urlpatterns = [
    path('', index, name='accounts_index'),  # test endpoint
    path('auth/register/', RegisterView.as_view(), name='register'),
]
