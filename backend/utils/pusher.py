# backend/utils/pusher.py
import pusher
from django.conf import settings

def get_pusher_client():
    """
    Initialize and return a Pusher client instance
    """
    pusher_client = pusher.Pusher(
        app_id=settings.PUSHER_APP_ID,
        key=settings.PUSHER_KEY,
        secret=settings.PUSHER_SECRET,
        cluster=settings.PUSHER_CLUSTER,
        ssl=settings.PUSHER_SSL
    )
    return pusher_client

# Singleton instance for reuse
pusher_client = get_pusher_client()

def trigger_notification(account_number, event_name, data):
    """
    Helper function to trigger a notification to a specific user
    
    Args:
        account_number: The user's account number (for private channel)
        event_name: The event name (e.g., 'notification.created')
        data: Dictionary of data to send
    """
    channel = f'private-user-{account_number}'
    try:
        pusher_client.trigger(channel, event_name, data)
        print(f" Pusher: Triggered {event_name} to {channel}")
        return True
    except Exception as e:
        print(f" Pusher error: {e}")
        return False
