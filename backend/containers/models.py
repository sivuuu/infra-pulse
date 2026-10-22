from django.db import models
from targets.models import HostTarget

class ContainerState(models.TextChoices):
    RUNNING = 'running', 'Running'
    EXITED = 'exited', 'Exited'
    PAUSED = 'paused', 'Paused'
    STOPPED = 'stopped', 'Stopped'
    DEAD = 'dead', 'Dead'
    UNKNOWN = 'unknown', 'Unknown'

class ContainerHealth(models.TextChoices):
    HEALTHY = 'healthy', 'Healthy'
    UNHEALTHY = 'unhealthy', 'Unhealthy'
    UNREACHABLE = 'unreachable', 'Unreachable'
    NONE = 'none', 'No Health Check'

class Container(models.Model):
    target = models.ForeignKey(HostTarget, on_delete=models.CASCADE, related_name='containers')
    container_id = models.CharField(max_length=128, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    image = models.CharField(max_length=255)
    runtime = models.CharField(max_length=32, default='podman')
    state = models.CharField(max_length=32, choices=ContainerState.choices, default=ContainerState.UNKNOWN, db_index=True)
    status = models.CharField(max_length=128, blank=True)
    health_status = models.CharField(max_length=32, choices=ContainerHealth.choices, default=ContainerHealth.NONE, db_index=True)
    created_at_runtime = models.DateTimeField(null=True, blank=True)
    restart_count = models.IntegerField(default=0)
    ports = models.JSONField(default=list, blank=True)
    labels = models.JSONField(default=dict, blank=True)
    env_keys = models.JSONField(default=list, blank=True)  # Strictly keys only, no secrets
    last_inspected = models.DateTimeField(null=True, blank=True)
    is_stale = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('target', 'container_id')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.container_id[:12]}) - {self.state}"
