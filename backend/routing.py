# routing.py
from django.urls import path
from consumers import PusherAuthConsumer  # Changed from . import consumers

websocket_urlpatterns = [
    path('ws/pusher/auth/', PusherAuthConsumer.as_asgi()),
]