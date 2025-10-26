from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

def get_supabase_client() -> Client:
    """
    Creates and returns a Supabase client using the project's URL and Key.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env file")

    return create_client(url, key)
