from django.db import models
from containers.models import Container

class LogLevel(models.TextChoices):
    DEBUG = 'DEBUG', 'Debug'
    INFO = 'INFO', 'Info'
    WARN = 'WARN', 'Warning'
    ERROR = 'ERROR', 'Error'
    FATAL = 'FATAL', 'Fatal'

class LogEntry(models.Model):
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name='logs', db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    level = models.CharField(max_length=16, choices=LogLevel.choices, default=LogLevel.INFO, db_index=True)
    source = models.CharField(max_length=32, default='stdout')  # stdout, stderr, runtime
    message = models.TextField()
    raw_message = models.TextField(blank=True)
    is_sensitive_redacted = models.BooleanField(default=False)
    related_incident_id = models.IntegerField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['container', '-timestamp']),
            models.Index(fields=['level', '-timestamp']),
        ]

    def __str__(self):
        return f"[{self.timestamp}] [{self.level}] ({self.container.name}): {self.message[:60]}"
