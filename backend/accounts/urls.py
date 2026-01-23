from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from . import views_basic

app_name = 'accounts'

urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Session Authentication
    path('login/', views_basic.login_view, name='login'),
    path('register/', views_basic.register_view, name='register'),
    path('user/', views_basic.get_user_view, name='get_user'),
    path('logout/', views_basic.logout_view, name='logout'),
]
