from django.contrib import admin
from .models import UserTask

@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'task', 'status', 'reward_earned', 'started_at')
    readonly_fields = ('started_at', 'completed_at')
