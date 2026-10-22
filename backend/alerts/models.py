from django.db import models
from django.contrib.auth.models import User
from containers.models import Container

class MetricType(models.TextChoices):
    CPU_PERCENT = 'cpu_percent', 'CPU Utilization (%)'
    MEMORY_PERCENT = 'memory_percent', 'Memory Utilization (%)'
    HEALTH_STATUS = 'health_status', 'Health Status'
    STATE = 'state', 'Container State'
    RESTART_COUNT = 'restart_count', 'Restart Count'
    REACHABILITY = 'reachability', 'Target Reachability'

class ConditionOperator(models.TextChoices):
    GT = '>', 'Greater than (>)'
    GTE = '>=', 'Greater than or equal (>=)'
    LT = '<', 'Less than (<)'
    LTE = '<=', 'Less than or equal (<=)'
    EQ = '==', 'Equals (==)'
    NEQ = '!=', 'Not equals (!=)'

class Severity(models.TextChoices):
    CRITICAL = 'critical', 'Critical'
    WARNING = 'warning', 'Warning'
    INFO = 'info', 'Info'

class IncidentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Evaluation'
    FIRING = 'firing', 'Firing'
    RESOLVED = 'resolved', 'Resolved'

class AlertRule(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    metric = models.CharField(max_length=64, choices=MetricType.choices, default=MetricType.CPU_PERCENT)
    condition = models.CharField(max_length=8, choices=ConditionOperator.choices, default=ConditionOperator.GT)
    threshold = models.FloatField(default=80.0, help_text="Numeric threshold, or 1/0 for state/reachability")
    threshold_str = models.CharField(max_length=64, blank=True, help_text="String threshold if evaluating string state (e.g. 'unhealthy', 'exited')")
    duration_seconds = models.IntegerField(default=30, help_text="Evaluation window before state changes from pending to firing")
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.WARNING)
    container_filter = models.CharField(max_length=255, default='*', help_text="Regex or substring filter for container names (* for all)")
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.metric} {self.condition} {self.threshold}) [{self.severity}]"


class Incident(models.Model):
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='incidents')
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name='incidents')
    status = models.CharField(max_length=16, choices=IncidentStatus.choices, default=IncidentStatus.PENDING, db_index=True)
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.WARNING)
    current_value = models.FloatField(null=True, blank=True)
    summary = models.TextField()
    first_seen = models.DateTimeField(db_index=True)
    last_seen = models.DateTimeField(db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='resolved_incidents')
    resolution_note = models.TextField(blank=True)
    dedup_key = models.CharField(max_length=255, db_index=True)  # rule_id:container_id
    storm_count = models.IntegerField(default=1, help_text="Count of consecutive breached evaluations deduplicated into this incident")

    class Meta:
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['status', '-last_seen']),
            models.Index(fields=['dedup_key', 'status']),
        ]

    def __str__(self):
        return f"[{self.status.upper()}] {self.rule.name} on {self.container.name} ({self.severity})"
