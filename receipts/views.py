from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from backend.supabase_storage import upload_receipt, list_user_receipts, generate_signed_url
import os

@csrf_exempt
@require_http_methods(["POST"])
def upload_receipt_view(request):
    """
    Handles a file upload from a user and sends it to Supabase Storage.
    """
    user_id = request.POST.get("user_id")
    file = request.FILES.get("file")

    if not user_id or not file:
        return JsonResponse({"error": "user_id and file are required"}, status=400)

    temp_path = f"/tmp/{file.name}"
    with open(temp_path, "wb+") as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    try:
        upload_receipt(user_id, temp_path, file.name)
        os.remove(temp_path)
        return JsonResponse({"message": "Upload successful", "file_name": file.name})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def list_receipts_view(request):
    """
    Lists all receipts for a given user.
    """
    user_id = request.GET.get("user_id")
    if not user_id:
        return JsonResponse({"error": "user_id is required"}, status=400)

    try:
        response = list_user_receipts(user_id)
        return JsonResponse({"files": response})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_signed_url_view(request):
    """
    Returns a signed URL for downloading a receipt.
    """
    user_id = request.GET.get("user_id")
    file_name = request.GET.get("file_name")

    if not user_id or not file_name:
        return JsonResponse({"error": "user_id and file_name are required"}, status=400)

    try:
        url = generate_signed_url(user_id, file_name)
        return JsonResponse({"signed_url": url})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
