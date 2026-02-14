from django.urls import path, include
from django.http import HttpResponse
from django.contrib import admin
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_GET
def health_check(request):
    return HttpResponse("OK", status=200, content_type="text/plain")

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('health', health_check, name='health_check_no_slash'),
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/users/', include('users.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/cards/', include('cards.urls')),  # ADD THIS LINE
]