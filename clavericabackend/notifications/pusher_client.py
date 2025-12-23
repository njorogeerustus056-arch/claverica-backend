# notifications/pusher_client.py

import os
import pusher

# Initialize Pusher client using env vars
pusher_client = pusher.Pusher(
    app_id=os.environ.get("PUSHER_APP_ID"),
    key=os.environ.get("PUSHER_KEY"),
    secret=os.environ.get("PUSHER_SECRET"),
    cluster=os.environ.get("PUSHER_CLUSTER"),
    ssl=True
)

def trigger_notification(user_id, event, data):
    """
    Trigger a Pusher event to a user-specific channel.
    
    Args:
        user_id (int): ID of the user
        event (str): Event name
        data (dict): Payload data
    """
    channel = f"user_{user_id}_notifications"
    pusher_client.trigger(channel, event, data)
