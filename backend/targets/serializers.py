from rest_framework import serializers
from .models import HostTarget

class HostTargetSerializer(serializers.ModelSerializer):
    containers_count = serializers.SerializerMethodField()
    running_containers_count = serializers.SerializerMethodField()

    class Meta:
        model = HostTarget
        fields = [
            'id', 'name', 'hostname', 'runtime_type', 'status',
            'collector_version', 'endpoint_url', 'last_seen',
            'error_message', 'metadata', 'created_at', 'updated_at',
            'containers_count', 'running_containers_count'
        ]

    def get_containers_count(self, obj):
        return obj.containers.count()

    def get_running_containers_count(self, obj):
        return obj.containers.filter(state='running').count()
