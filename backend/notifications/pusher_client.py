# notifications/pusher_client.py

import pusher
from django.conf import settings

def get_pusher_client():
    """
    Lazily initialize and return a Pusher client.
    Prevents Django startup crashes if env vars are missing.
    """
    if not all([
        settings.PUSHER_APP_ID,
        settings.PUSHER_KEY,
        settings.PUSHER_SECRET,
        settings.PUSHER_CLUSTER
    ]):
        return None

    return pusher.Pusher(
        app_id=settings.PUSHER_APP_ID,
        key=settings.PUSHER_KEY,
        secret=settings.PUSHER_SECRET,
        cluster=settings.PUSHER_CLUSTER,
        ssl=True
    )

def trigger_notification(user_id, event, data):
    """
    Trigger a Pusher event to a user-specific channel.
    Uses consistent channel naming: user-{user_id}
    """
    client = get_pusher_client()
    if not client:
        return  # Safe no-op if Pusher is not configured

    channel = f"user-{user_id}"  # ✅ Changed to match utils.py
    try:
        client.trigger(channel, event, data)
    except Exception as e:
        # Log error but don't crash
        print(f"⚠️ Pusher error: {e}")