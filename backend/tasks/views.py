from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import TaskCategory, ClavericaTask
from .serializers import TaskCategorySerializer, ClavericaTaskSerializer

class TaskCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TaskCategory.objects.filter(is_active=True).order_by('display_order')
    serializer_class = TaskCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ClavericaTaskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ClavericaTaskSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = ClavericaTask.objects.filter(status='active')
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        tasks = ClavericaTask.objects.filter(status='active')[:10]
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
