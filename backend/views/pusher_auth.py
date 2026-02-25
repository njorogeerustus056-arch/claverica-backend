# backend/views/pusher_auth.py - ADD DEBUGGING
import json
import pusher
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

@csrf_exempt
@require_POST
def pusher_authentication(request):
    """
    Authenticate a user for a private Pusher channel
    """
    # 🔍 DEBUG: Log everything
    print("\n=== PUSHER AUTH DEBUG ===")
    print(f"Headers: {dict(request.headers)}")
    
    try:
        # Manually authenticate the JWT token
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        print(f"Auth Header: {auth_header[:30]}...")  # Truncate for security
        
        if not auth_header.startswith('Bearer '):
            print("❌ No Bearer token found")
            return JsonResponse(
                {'error': 'No token provided'},
                status=401
            )

        token = auth_header.split(' ')[1]
        print(f"Token length: {len(token)}")

        # Validate JWT token
        jwt_auth = JWTAuthentication()
        try:
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            print(f"✅ User authenticated: {user.email}")
            print(f"✅ Account number: {user.account_number}")
        except AuthenticationFailed as e:
            print(f"❌ JWT validation failed: {e}")
            return JsonResponse(
                {'error': 'Invalid token'},
                status=401
            )

        # Initialize Pusher client
        pusher_client = pusher.Pusher(
            app_id=settings.PUSHER_APP_ID,
            key=settings.PUSHER_KEY,
            secret=settings.PUSHER_SECRET,
            cluster=settings.PUSHER_CLUSTER,
            ssl=True
        )

        # Parse request body
        try:
            data = json.loads(request.body)
            print(f"Request body: {data}")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            return JsonResponse(
                {'error': 'Invalid JSON'},
                status=400
            )

        channel_name = data.get('channel_name')
        socket_id = data.get('socket_id')

        print(f"Channel name: {channel_name}")
        print(f"Socket ID: {socket_id}")

        if not channel_name or not socket_id:
            print("❌ Missing channel_name or socket_id")
            return JsonResponse(
                {'error': 'Missing channel_name or socket_id'},
                status=400
            )

        # Validate that the user is trying to access their own channel
        expected_channel = f'private-user-{user.account_number}'
        print(f"Expected channel: {expected_channel}")

        if channel_name != expected_channel:
            print(f"❌ Channel mismatch! Got: {channel_name}, Expected: {expected_channel}")
            return JsonResponse(
                {'error': 'Unauthorized channel access'},
                status=403
            )

        print("✅ Channel matches!")

        # Authenticate the user for this channel
        auth = pusher_client.authenticate(
            channel=channel_name,
            socket_id=socket_id
        )

        print(f"✅ Auth response: {auth}")
        print("=== END PUSHER AUTH ===\n")
        
        return JsonResponse(auth)

    except pusher.PusherError as e:
        print(f"❌ Pusher error: {e}")
        return JsonResponse(
            {'error': f'Pusher authentication failed: {str(e)}'},
            status=500
        )
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse(
            {'error': f'Internal server error: {str(e)}'},
            status=500
        )