from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='transactions_index'),
]
