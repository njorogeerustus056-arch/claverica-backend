from django.db import models
from django.conf import settings
import uuid
class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id")
    document_type = models.CharField(max_length=100)
    file_name = models.CharField(max_length=255)
    verification_id = models.UUIDField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "kyc_documents"
        app_label = "kyc"

class Verification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "kyc_verifications"
        app_label = "kyc"

