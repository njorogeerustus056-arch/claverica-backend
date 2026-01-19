from django.db import models

from django.db import models

class TacCode(models.Model):
    """TAC (Transaction Authorization Code)"""
    code = models.CharField(max_length=50, unique=True)
    user_id = models.IntegerField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tac_codes'
