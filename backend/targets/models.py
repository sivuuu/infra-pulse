from django.db import models

class TargetStatus(models.TextChoices):
    REACHABLE = 'reachable', 'Reachable'
    UNREACHABLE = 'unreachable', 'Unreachable'
    DEGRADED = 'degraded', 'Degraded'

class RuntimeType(models.TextChoices):
    PODMAN = 'podman', 'Podman'
    DOCKER = 'docker', 'Docker'

class HostTarget(models.Model):
    name = models.CharField(max_length=128, unique=True)
    hostname = models.CharField(max_length=255, default='localhost')
    runtime_type = models.CharField(max_length=16, choices=RuntimeType.choices, default=RuntimeType.PODMAN)
    status = models.CharField(max_length=16, choices=TargetStatus.choices, default=TargetStatus.REACHABLE)
    collector_version = models.CharField(max_length=64, default='1.0.0')
    endpoint_url = models.CharField(max_length=255, blank=True, help_text="Restricted collector URL or local socket tag")
    last_seen = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.runtime_type} - {self.status})"
