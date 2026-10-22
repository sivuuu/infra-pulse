from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Container
from .serializers import ContainerListSerializer, ContainerDetailSerializer
from metrics.models import MetricSample
from logs.models import LogEntry
from logs.serializers import LogEntrySerializer
from core.models import AuditLog
from core.permissions import IsAdminOrReadOnly, IsAdminUserOnly
from runtime.factory import get_runtime_adapter

class ContainerViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ContainerDetailSerializer
        return ContainerListSerializer

    def get_queryset(self):
        qs = Container.objects.all().select_related('target')

        target_param = self.request.query_params.get('target') or self.request.query_params.get('host')
        if target_param:
            qs = qs.filter(Q(target__name__icontains=target_param) | Q(target__hostname__icontains=target_param))

        state_param = self.request.query_params.get('state')
        if state_param:
            qs = qs.filter(state__iexact=state_param)

        runtime_param = self.request.query_params.get('runtime')
        if runtime_param:
            qs = qs.filter(runtime__iexact=runtime_param)

        service_param = self.request.query_params.get('service')
        if service_param:
            qs = qs.filter(Q(name__icontains=service_param) | Q(labels__icontains=service_param))

        health_param = self.request.query_params.get('health')
        if health_param:
            qs = qs.filter(health_status__iexact=health_param)

        search_param = self.request.query_params.get('search')
        if search_param:
            qs = qs.filter(
                Q(name__icontains=search_param) |
                Q(container_id__icontains=search_param) |
                Q(image__icontains=search_param)
            )

        # Attach latest metric sample and active incident count efficiently
        container_list = list(qs)
        for c in container_list:
            c._latest_metric = MetricSample.objects.filter(container=c, is_available=True).order_by('-timestamp').first()
            c._active_incidents_count = c.incidents.filter(status__in=['pending', 'firing']).count()

        return container_list

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserOnly])
    def restart(self, request, pk=None):
        container = self.get_object()
        adapter = get_runtime_adapter()
        success = adapter.restart_container(container.container_id)

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action='CONTAINER_RESTART',
            target_type='container',
            target_id=container.container_id[:12],
            details={
                'container_name': container.name,
                'target': container.target.name,
                'success': success
            },
            ip_address=request.META.get('REMOTE_ADDR')
        )

        if success:
            container.state = 'running'
            container.restart_count += 1
            container.save(update_fields=['state', 'restart_count'])
            return Response({"status": "success", "message": f"Container {container.name} restarted successfully."})
        return Response({"status": "error", "message": f"Failed to restart container {container.name} via runtime adapter."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserOnly])
    def stop(self, request, pk=None):
        container = self.get_object()
        adapter = get_runtime_adapter()
        success = adapter.stop_container(container.container_id)

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action='CONTAINER_STOP',
            target_type='container',
            target_id=container.container_id[:12],
            details={
                'container_name': container.name,
                'target': container.target.name,
                'success': success
            },
            ip_address=request.META.get('REMOTE_ADDR')
        )

        if success:
            container.state = 'stopped'
            container.save(update_fields=['state'])
            return Response({"status": "success", "message": f"Container {container.name} stopped."})
        return Response({"status": "error", "message": f"Failed to stop container {container.name} via runtime adapter."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """Fetch time-series metrics for this container with windowing."""
        container = self.get_object()
        window = request.query_params.get('window', '1h')
        
        limit_points = 60
        if window == '5m':
            limit_points = 20
        elif window == '15m':
            limit_points = 45
        elif window == '6h':
            limit_points = 120
        elif window == '24h':
            limit_points = 240

        samples = MetricSample.objects.filter(
            container=container,
            is_available=True
        ).order_by('-timestamp')[:limit_points]

        data = [
            {
                "timestamp": s.timestamp.isoformat(),
                "cpu_percent": s.cpu_percent,
                "memory_usage_bytes": s.memory_usage_bytes,
                "memory_limit_bytes": s.memory_limit_bytes,
                "memory_percent": s.memory_percent,
                "net_rx_bytes": s.net_rx_bytes,
                "net_tx_bytes": s.net_tx_bytes,
                "block_read_bytes": s.block_read_bytes,
                "block_write_bytes": s.block_write_bytes,
                "pids": s.pids_count
            }
            for s in reversed(list(samples))
        ]
        return Response({"container_id": container.container_id, "window": window, "points": data})

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Fetch recent sanitized logs for this container."""
        container = self.get_object()
        limit = min(int(request.query_params.get('limit', 100)), 500)
        logs = LogEntry.objects.filter(container=container).order_by('-timestamp')[:limit]
        serializer = LogEntrySerializer(logs, many=True)
        return Response(serializer.data)
