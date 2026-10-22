from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.utils import timezone as dj_timezone
from datetime import timedelta
from django.db.models import Avg, Sum, Count, Q
from containers.models import Container, ContainerHealth, ContainerState
from targets.models import HostTarget, TargetStatus
from .models import MetricSample
from .serializers import MetricSampleSerializer
from .prometheus import get_metrics_prometheus_response
from alerts.models import Incident, IncidentStatus

class MetricSummaryView(APIView):
    """Provides high-level KPI metrics for the executive dashboard."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        now = dj_timezone.now()
        targets = HostTarget.objects.all()
        containers = Container.objects.all()

        total_containers = containers.count()
        running_containers = containers.filter(state=ContainerState.RUNNING).count()
        stopped_containers = containers.filter(state__in=[ContainerState.STOPPED, ContainerState.EXITED]).count()
        healthy_containers = containers.filter(health_status=ContainerHealth.HEALTHY).count()
        unhealthy_containers = containers.filter(health_status=ContainerHealth.UNHEALTHY).count()
        unreachable_containers = containers.filter(
            Q(health_status=ContainerHealth.UNHEALTHY) |
            Q(target__status=TargetStatus.UNREACHABLE) |
            Q(is_stale=True)
        ).count()

        # Latest metrics aggregation across active running containers
        latest_samples = []
        for c in containers.filter(state=ContainerState.RUNNING):
            s = MetricSample.objects.filter(container=c, is_available=True).order_by('-timestamp').first()
            if s:
                latest_samples.append(s)

        avg_cpu = round(sum(s.cpu_percent for s in latest_samples if s.cpu_percent is not None) / len(latest_samples), 2) if latest_samples else 0.0
        avg_mem_percent = round(sum(s.memory_percent for s in latest_samples if s.memory_percent is not None) / len(latest_samples), 2) if latest_samples else 0.0
        total_mem_usage = sum(s.memory_usage_bytes for s in latest_samples if s.memory_usage_bytes is not None)
        total_net_rx = sum(s.net_rx_bytes for s in latest_samples if s.net_rx_bytes is not None)
        total_net_tx = sum(s.net_tx_bytes for s in latest_samples if s.net_tx_bytes is not None)

        # Incident metrics
        firing_incidents = Incident.objects.filter(status=IncidentStatus.FIRING).count()
        pending_incidents = Incident.objects.filter(status=IncidentStatus.PENDING).count()
        critical_incidents = Incident.objects.filter(status=IncidentStatus.FIRING, severity='critical').count()

        # Collector status
        last_seen_target = targets.order_by('-last_seen').first()
        collector_healthy = targets.filter(status=TargetStatus.REACHABLE).exists() if targets.exists() else False

        data_freshness_seconds = None
        if last_seen_target and last_seen_target.last_seen:
            data_freshness_seconds = int((now - last_seen_target.last_seen).total_seconds())

        return Response({
            "containers": {
                "total": total_containers,
                "running": running_containers,
                "stopped": stopped_containers,
                "healthy": healthy_containers,
                "unhealthy": unhealthy_containers,
                "unreachable": unreachable_containers,
            },
            "system_metrics": {
                "average_cpu_percent": avg_cpu,
                "average_memory_percent": avg_mem_percent,
                "total_memory_usage_bytes": total_mem_usage,
                "total_net_rx_bytes": total_net_rx,
                "total_net_tx_bytes": total_net_tx,
            },
            "alerts": {
                "firing": firing_incidents,
                "pending": pending_incidents,
                "critical": critical_incidents,
            },
            "collector": {
                "status": "healthy" if collector_healthy else "unreachable",
                "targets_count": targets.count(),
                "last_collection": last_seen_target.last_seen if last_seen_target else None,
                "freshness_seconds": data_freshness_seconds,
            },
            "timestamp": now.isoformat()
        })


class TimeSeriesMetricsView(APIView):
    """
    Returns aggregated time-series telemetry points across all containers
    for system-wide trend charts with selectable time window.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        window = request.query_params.get('window', '1h')
        limit = 60
        if window == '5m':
            limit = 20
        elif window == '15m':
            limit = 45
        elif window == '6h':
            limit = 120
        elif window == '24h':
            limit = 240

        # Query recent distinct timestamps
        recent_timestamps = list(
            MetricSample.objects.filter(is_available=True)
            .values_list('timestamp', flat=True)
            .order_by('-timestamp')
            .distinct()[:limit]
        )
        recent_timestamps.reverse()

        points = []
        for ts in recent_timestamps:
            samples = MetricSample.objects.filter(timestamp=ts, is_available=True)
            cpu_vals = [s.cpu_percent for s in samples if s.cpu_percent is not None]
            mem_vals = [s.memory_percent for s in samples if s.memory_percent is not None]
            mem_bytes = [s.memory_usage_bytes for s in samples if s.memory_usage_bytes is not None]

            points.append({
                "timestamp": ts.isoformat(),
                "avg_cpu_percent": round(sum(cpu_vals) / len(cpu_vals), 2) if cpu_vals else 0.0,
                "avg_memory_percent": round(sum(mem_vals) / len(mem_vals), 2) if mem_vals else 0.0,
                "total_memory_bytes": sum(mem_bytes),
                "active_samples": len(samples)
            })

        return Response({
            "window": window,
            "points": points
        })


class PrometheusMetricsView(APIView):
    """Prometheus exposition format endpoint."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return get_metrics_prometheus_response()
