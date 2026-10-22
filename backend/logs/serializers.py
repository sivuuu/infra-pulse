from rest_framework import serializers
from .models import LogEntry

class LogEntrySerializer(serializers.ModelSerializer):
    container_name = serializers.CharField(source='container.name', read_only=True)
    short_container_id = serializers.SerializerMethodField()

    class Meta:
        model = LogEntry
        fields = [
            'id', 'container', 'container_name', 'short_container_id',
            'timestamp', 'level', 'source', 'message',
            'is_sensitive_redacted', 'related_incident_id', 'created_at'
        ]

    def get_short_container_id(self, obj):
        return obj.container.container_id[:12] if obj.container else ""
