import requests
import json
import os

# -----------------------------
# Configuration
# -----------------------------
BASE_URL = "http://127.0.0.1:8000/api/receipts"
USER_ID = "12345"  # 👈 Replace this if your backend expects a real user_id
FILE_PATH = r"D:\Documents\invoice.pdf"  # 👈 Your actual test file path

# -----------------------------
# 1️⃣ Upload Receipt
# -----------------------------
def upload_receipt():
    print("\n🔼 Uploading receipt...")

    # Check file existence
    if not os.path.exists(FILE_PATH):
        print(f"❌ File not found at {FILE_PATH}")
        return None

    url = f"{BASE_URL}/upload/"
    data = {"user_id": USER_ID}

    try:
        with open(FILE_PATH, "rb") as file:
            files = {"file": file}
            response = requests.post(url, data=data, files=files)
    except Exception as e:
        print(f"❌ Error opening file: {e}")
        return None

    print("Status Code:", response.status_code)
    print("Response:", response.text)
    return response


# -----------------------------
# 2️⃣ List User Receipts
# -----------------------------
def list_receipts():
    print("\n📄 Listing user receipts...")
    url = f"{BASE_URL}/list/"
    params = {"user_id": USER_ID}

    try:
        response = requests.get(url, params=params)
        print("Status Code:", response.status_code)
        print(json.dumps(response.json(), indent=4))
    except Exception as e:
        print(f"❌ Error listing receipts: {e}")
    return response


# -----------------------------
# 3️⃣ Generate Signed URL
# -----------------------------
def generate_signed_url(file_name):
    print("\n🔗 Generating signed URL...")
    url = f"{BASE_URL}/signed-url/"
    params = {"user_id": USER_ID, "file_name": file_name}

    try:
        response = requests.get(url, params=params)
        print("Status Code:", response.status_code)
        data = response.json()
        print(json.dumps(data, indent=4))
        return data.get("signed_url")
    except Exception as e:
        print(f"❌ Error generating signed URL: {e}")
        return None


# -----------------------------
# MAIN TEST SEQUENCE
# -----------------------------
if __name__ == "__main__":
    print("🚀 Starting API test sequence...")

    # 1️⃣ Upload receipt
    upload_resp = upload_receipt()

    # 2️⃣ List receipts (confirm upload)
    list_resp = list_receipts()

    # 3️⃣ Generate signed URL (download link)
    if upload_resp and upload_resp.status_code == 200:
        uploaded_file = os.path.basename(FILE_PATH)
        generate_signed_url(uploaded_file)
    else:
        print("\n⚠️ Skipping signed URL generation (upload failed).")

    print("\n✅ Test sequence complete.")
