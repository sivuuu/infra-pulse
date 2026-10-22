from rest_framework import serializers
from .models import AlertRule, Incident

class AlertRuleSerializer(serializers.ModelSerializer):
    active_incidents_count = serializers.SerializerMethodField()

    class Meta:
        model = AlertRule
        fields = [
            'id', 'name', 'description', 'metric', 'condition',
            'threshold', 'threshold_str', 'duration_seconds', 'severity',
            'container_filter', 'enabled', 'active_incidents_count',
            'created_at', 'updated_at'
        ]

    def get_active_incidents_count(self, obj):
        return obj.incidents.filter(status__in=['pending', 'firing']).count()


class IncidentSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    rule_metric = serializers.CharField(source='rule.metric', read_only=True)
    container_name = serializers.CharField(source='container.name', read_only=True)
    short_container_id = serializers.SerializerMethodField()
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True)
    duration_active_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            'id', 'rule', 'rule_name', 'rule_metric', 'container',
            'container_name', 'short_container_id', 'status', 'severity',
            'current_value', 'summary', 'first_seen', 'last_seen',
            'resolved_at', 'resolved_by', 'resolved_by_username',
            'resolution_note', 'dedup_key', 'storm_count',
            'duration_active_seconds'
        ]

    def get_short_container_id(self, obj):
        return obj.container.container_id[:12] if obj.container else ""

    def get_duration_active_seconds(self, obj):
        end = obj.resolved_at or obj.last_seen
        return int((end - obj.first_seen).total_seconds()) if (end and obj.first_seen) else 0
