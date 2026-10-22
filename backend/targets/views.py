from rest_framework import viewsets, permissions
from .models import HostTarget
from .serializers import HostTargetSerializer
from core.permissions import IsAdminOrReadOnly

class HostTargetViewSet(viewsets.ModelViewSet):
    queryset = HostTarget.objects.all().prefetch_related('containers')
    serializer_class = HostTargetSerializer
    permission_classes = [IsAdminOrReadOnly]
