from django.urls import path, include
from django.http import HttpResponse
from django.contrib import admin
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from views.pusher_auth import pusher_authentication
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

@csrf_exempt
@require_GET
def health_check(request):
    return HttpResponse("OK", status=200, content_type="text/plain")

@csrf_exempt
@require_GET
def detailed_health_check(request):
    from django.db import connections
    from django.db.utils import OperationalError

    health_status = {
        'status': 'healthy',
        'database': 'connected',
        'timestamp': str(timezone.now()),
    }

    try:
        db_conn = connections['default']
        db_conn.cursor().execute('SELECT 1')
    except OperationalError:
        health_status['status'] = 'unhealthy'
        health_status['database'] = 'disconnected'
        return HttpResponse(
            json.dumps(health_status),
            status=500,
            content_type="application/json"
        )

    return HttpResponse(
        json.dumps(health_status),
        status=200,
        content_type="application/json"
    )

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('health', health_check, name='health_check_no_slash'),
    path('health/detailed/', detailed_health_check, name='detailed_health'),
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/pusher/auth/', pusher_authentication, name='pusher_auth'),
    path('api/accounts/', include('accounts.urls')),
    path('api/users/', include('users.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/cards/', include('cards.urls')),
    path('api/compliance/', include('compliance.urls')),
    path('api/kyc/', include('kyc.urls')),
    path('api/kyc_spec/', include('kyc_spec.urls')),
    path('api/transfers/', include('transfers.urls')),
]