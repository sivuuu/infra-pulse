from rest_framework import serializers
from .models import Container
from metrics.models import MetricSample

class ContainerListSerializer(serializers.ModelSerializer):
    target_name = serializers.CharField(source='target.name', read_only=True)
    target_status = serializers.CharField(source='target.status', read_only=True)
    short_id = serializers.SerializerMethodField()
    cpu_percent = serializers.SerializerMethodField()
    memory_percent = serializers.SerializerMethodField()
    active_incidents_count = serializers.SerializerMethodField()

    class Meta:
        model = Container
        fields = [
            'id', 'container_id', 'short_id', 'name', 'image', 'runtime',
            'state', 'status', 'health_status', 'created_at_runtime',
            'restart_count', 'ports', 'labels', 'is_stale', 'last_inspected',
            'target_name', 'target_status', 'cpu_percent', 'memory_percent',
            'active_incidents_count'
        ]

    def get_short_id(self, obj):
        return obj.container_id[:12] if obj.container_id else ""

    def get_cpu_percent(self, obj):
        latest = getattr(obj, '_latest_metric', None)
        if latest and latest.is_available:
            return latest.cpu_percent
        return None

    def get_memory_percent(self, obj):
        latest = getattr(obj, '_latest_metric', None)
        if latest and latest.is_available:
            return latest.memory_percent
        return None

    def get_active_incidents_count(self, obj):
        return getattr(obj, '_active_incidents_count', 0)


class ContainerDetailSerializer(serializers.ModelSerializer):
    target_name = serializers.CharField(source='target.name', read_only=True)
    target_status = serializers.CharField(source='target.status', read_only=True)
    short_id = serializers.SerializerMethodField()
    latest_metrics = serializers.SerializerMethodField()
    active_incidents = serializers.SerializerMethodField()

    class Meta:
        model = Container
        fields = [
            'id', 'container_id', 'short_id', 'name', 'image', 'runtime',
            'state', 'status', 'health_status', 'created_at_runtime',
            'restart_count', 'ports', 'labels', 'env_keys', 'is_stale',
            'last_inspected', 'target_name', 'target_status',
            'latest_metrics', 'active_incidents', 'created_at', 'updated_at'
        ]

    def get_short_id(self, obj):
        return obj.container_id[:12] if obj.container_id else ""

    def get_latest_metrics(self, obj):
        latest = MetricSample.objects.filter(container=obj, is_available=True).order_by('-timestamp').first()
        if not latest:
            return None
        return {
            "timestamp": latest.timestamp,
            "cpu_percent": latest.cpu_percent,
            "memory_usage_bytes": latest.memory_usage_bytes,
            "memory_limit_bytes": latest.memory_limit_bytes,
            "memory_percent": latest.memory_percent,
            "net_rx_bytes": latest.net_rx_bytes,
            "net_tx_bytes": latest.net_tx_bytes,
            "block_read_bytes": latest.block_read_bytes,
            "block_write_bytes": latest.block_write_bytes,
            "pids_count": latest.pids_count,
            "is_available": latest.is_available,
        }

    def get_active_incidents(self, obj):
        incidents = obj.incidents.filter(status__in=['pending', 'firing']).select_related('rule')
        return [
            {
                "id": inc.id,
                "rule_name": inc.rule.name,
                "severity": inc.severity,
                "status": inc.status,
                "summary": inc.summary,
                "first_seen": inc.first_seen,
                "last_seen": inc.last_seen,
            }
            for inc in incidents
        ]
