from django.urls import path
from . import views

urlpatterns = [
    # Base endpoint
    path('', views.index, name='transactions_index'),
    
    # CRUD operations
    path('create/', views.create_transaction_view, name='create_transaction'),
    path('list/', views.list_transactions_view, name='list_transactions'),
    path('<int:transaction_id>/', views.get_transaction_detail_view, name='transaction_detail'),
    path('<int:transaction_id>/update/', views.update_transaction_view, name='update_transaction'),
    path('<int:transaction_id>/delete/', views.delete_transaction_view, name='delete_transaction'),
    
    # Stats and analytics
    path('stats/', views.get_transaction_stats_view, name='transaction_stats'),
    path('recent/', views.get_recent_activity_view, name='recent_activity'),
]