from supabase import create_client, Client
from dotenv import load_dotenv
import os
import mimetypes  # ✅ for auto-detecting file types

# Load .env variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ Warning: Supabase credentials not loaded from .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_receipt(user_id: str, file_path: str, file_name: str):
    """
    Uploads a file to the 'receipts' bucket for a specific user.
    Automatically detects the MIME type (e.g., PDF, image, etc.).
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        storage_path = f"{user_id}/{file_name}"
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"  # fallback

        with open(file_path, "rb") as f:
            response = supabase.storage.from_("receipts").upload(
                storage_path,
                f,
                {"content-type": mime_type}  # ✅ auto MIME type
            )
        print(f"✅ Upload complete: {file_name} ({mime_type})")
        print(response)
    except Exception as e:
        print("❌ Upload failed:", e)


def list_user_receipts(user_id: str):
    """
    Lists all files under a user's folder in the 'receipts' bucket.
    """
    try:
        response = supabase.storage.from_("receipts").list(path=user_id)
        print("📄 Files:", response)
    except Exception as e:
        print("❌ Failed to list files:", e)


def generate_signed_url(user_id: str, file_name: str, expires_in: int = 3600):
    """
    Generates a temporary signed URL (valid for 1 hour by default)
    """
    try:
        storage_path = f"{user_id}/{file_name}"
        response = supabase.storage.from_("receipts").create_signed_url(storage_path, expires_in)
        if "signedURL" in response:
            print("🔗 Signed URL:", response["signedURL"])
            return response["signedURL"]
        else:
            print("⚠️ No signed URL returned:", response)
    except Exception as e:
        print("❌ Failed to create signed URL:", e)
