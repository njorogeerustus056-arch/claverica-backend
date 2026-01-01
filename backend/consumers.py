# backend/consumers.py
import json
import pusher
from channels.generic.http import AsyncHttpConsumer
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model

User = get_user_model()

class PusherAuthConsumer(AsyncHttpConsumer):
    async def handle(self, body):
        try:
            # Parse the request body
            data = json.loads(body.decode('utf-8'))
            socket_id = data.get('socket_id')
            channel_name = data.get('channel_name')
            
            if not socket_id or not channel_name:
                await self.send_response(400, b'{"error": "Missing socket_id or channel_name"}')
                return
            
            # Get authorization header
            headers = dict(self.scope['headers'])
            auth_header = None
            
            for key, value in headers.items():
                if key.lower() == b'authorization':
                    auth_header = value.decode()
                    break
            
            if not auth_header or not auth_header.startswith('Bearer '):
                await self.send_response(403, b'{"error": "No token provided"}')
                return
            
            token = auth_header.split(' ')[1]
            
            # Authenticate JWT token
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            
            if not user or isinstance(user, AnonymousUser):
                await self.send_response(403, b'{"error": "Invalid token"}')
                return
            
            # Initialize Pusher client
            pusher_client = pusher.Pusher(
                app_id=settings.PUSHER_APP_ID,
                key=settings.PUSHER_KEY,
                secret=settings.PUSHER_SECRET,
                cluster=settings.PUSHER_CLUSTER,
                ssl=True
            )
            
            # Generate auth response
            auth = pusher_client.authenticate(
                channel=channel_name,
                socket_id=socket_id
            )
            
            await self.send_response(
                200,
                json.dumps(auth).encode('utf-8'),
                headers=[
                    (b"Content-Type", b"application/json"),
                ]
            )
            
        except Exception as e:
            print(f"Pusher auth error: {str(e)}")
            await self.send_response(
                500, 
                json.dumps({"error": str(e)}).encode('utf-8')
            )