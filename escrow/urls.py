from django.urls import path
from . import views

urlpatterns = [
    # Base endpoint
    path('', views.index, name='escrow_index'),
    
    # CRUD operations
    path('create/', views.create_escrow_view, name='create_escrow'),
    path('list/', views.list_escrows_view, name='list_escrows'),
    path('<uuid:escrow_id>/', views.get_escrow_detail_view, name='escrow_detail'),
    path('<uuid:escrow_id>/update/', views.update_escrow_view, name='update_escrow'),
    
    # Escrow actions
    path('<uuid:escrow_id>/fund/', views.fund_escrow_view, name='fund_escrow'),
    path('<uuid:escrow_id>/release/', views.release_escrow_view, name='release_escrow'),
    path('<uuid:escrow_id>/dispute/', views.dispute_escrow_view, name='dispute_escrow'),
    
    # Stats
    path('stats/', views.get_escrow_stats_view, name='escrow_stats'),
]
