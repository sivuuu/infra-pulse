from rest_framework import serializers
from .models import MetricSample

class MetricSampleSerializer(serializers.ModelSerializer):
    container_name = serializers.CharField(source='container.name', read_only=True)

    class Meta:
        model = MetricSample
        fields = [
            'id', 'container', 'container_name', 'timestamp',
            'cpu_percent', 'memory_usage_bytes', 'memory_limit_bytes',
            'memory_percent', 'net_rx_bytes', 'net_tx_bytes',
            'block_read_bytes', 'block_write_bytes', 'pids_count',
            'is_available', 'error_note'
        ]
