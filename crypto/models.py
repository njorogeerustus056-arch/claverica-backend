# crypto/models.py
from django.db import models

# Example model
class Crypto(models.Model):
    name = models.CharField(max_length=100)
    value = models.FloatField()

    def __str__(self):
        return self.name
