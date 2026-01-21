from rest_framework import serializers
from .models import TaskCategory, ClavericaTask

class TaskCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskCategory
        fields = ['id', 'name', 'description', 'icon', 'color', 'display_order', 'created_at']

class ClavericaTaskSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    
    class Meta:
        model = ClavericaTask
        fields = ['id', 'title', 'description', 'reward_amount', 'status', 
                 'category', 'category_name', 'category_color', 'created_at']
