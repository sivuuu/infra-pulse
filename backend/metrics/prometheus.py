from prometheus_client import Gauge, Counter, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from django.http import HttpResponse
from containers.models import Container, ContainerHealth, ContainerState
from targets.models import HostTarget, TargetStatus
from metrics.models import MetricSample
from alerts.models import Incident, IncidentStatus

def get_metrics_prometheus_response():
    """
    Generate real-time Prometheus exposition format output
    derived from current database telemetry.
    """
    registry = CollectorRegistry()

    # Target reachability
    g_target_up = Gauge('infrapulse_target_up', 'Target reachable status (1=reachable, 0=unreachable)', ['target', 'runtime_type'], registry=registry)
    for t in HostTarget.objects.all():
        g_target_up.labels(target=t.name, runtime_type=t.runtime_type).set(1 if t.status == TargetStatus.REACHABLE else 0)

    # Container metrics
    g_cpu = Gauge('container_cpu_usage_percent', 'Current container CPU percentage', ['container_name', 'container_id', 'target', 'state'], registry=registry)
    g_mem_bytes = Gauge('container_memory_usage_bytes', 'Current container Memory usage in bytes', ['container_name', 'container_id', 'target', 'state'], registry=registry)
    g_mem_limit = Gauge('container_memory_limit_bytes', 'Container Memory limit in bytes', ['container_name', 'container_id', 'target'], registry=registry)
    g_mem_percent = Gauge('container_memory_usage_percent', 'Container Memory usage percent', ['container_name', 'container_id', 'target'], registry=registry)
    g_net_rx = Gauge('container_network_receive_bytes_total', 'Network receive bytes total', ['container_name', 'container_id'], registry=registry)
    g_net_tx = Gauge('container_network_transmit_bytes_total', 'Network transmit bytes total', ['container_name', 'container_id'], registry=registry)
    g_pids = Gauge('container_pids_count', 'Active container processes count', ['container_name', 'container_id'], registry=registry)
    g_health = Gauge('container_health_status', 'Container health check status (1=healthy, 0=unhealthy/unreachable)', ['container_name', 'container_id', 'health'], registry=registry)

    containers = Container.objects.all().select_related('target')
    for c in containers:
        latest = MetricSample.objects.filter(container=c, is_available=True).order_by('-timestamp').first()
        short_id = c.container_id[:12]
        target_name = c.target.name
        
        # Health metric
        is_healthy = 1 if c.health_status == ContainerHealth.HEALTHY else 0
        g_health.labels(container_name=c.name, container_id=short_id, health=c.health_status).set(is_healthy)

        if latest:
            if latest.cpu_percent is not None:
                g_cpu.labels(container_name=c.name, container_id=short_id, target=target_name, state=c.state).set(latest.cpu_percent)
            if latest.memory_usage_bytes is not None:
                g_mem_bytes.labels(container_name=c.name, container_id=short_id, target=target_name, state=c.state).set(latest.memory_usage_bytes)
            if latest.memory_limit_bytes is not None:
                g_mem_limit.labels(container_name=c.name, container_id=short_id, target=target_name).set(latest.memory_limit_bytes)
            if latest.memory_percent is not None:
                g_mem_percent.labels(container_name=c.name, container_id=short_id, target=target_name).set(latest.memory_percent)
            if latest.net_rx_bytes is not None:
                g_net_rx.labels(container_name=c.name, container_id=short_id).set(latest.net_rx_bytes)
            if latest.net_tx_bytes is not None:
                g_net_tx.labels(container_name=c.name, container_id=short_id).set(latest.net_tx_bytes)
            if latest.pids_count is not None:
                g_pids.labels(container_name=c.name, container_id=short_id).set(latest.pids_count)

    # Active Incidents metric
    g_incidents = Gauge('infrapulse_active_incidents', 'Count of active incidents', ['severity', 'status'], registry=registry)
    for status_choice in [IncidentStatus.PENDING, IncidentStatus.FIRING]:
        for sev in ['critical', 'warning', 'info']:
            cnt = Incident.objects.filter(status=status_choice, severity=sev).count()
            g_incidents.labels(severity=sev, status=status_choice).set(cnt)

    output = generate_latest(registry)
    return HttpResponse(output, content_type=CONTENT_TYPE_LATEST)
