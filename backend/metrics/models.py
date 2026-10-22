from django.db import models
from containers.models import Container

class MetricSample(models.Model):
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name='metrics', db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    
    # CPU
    cpu_percent = models.FloatField(null=True, blank=True)
    
    # Memory
    memory_usage_bytes = models.BigIntegerField(null=True, blank=True)
    memory_limit_bytes = models.BigIntegerField(null=True, blank=True)
    memory_percent = models.FloatField(null=True, blank=True)
    
    # Network I/O
    net_rx_bytes = models.BigIntegerField(null=True, blank=True)
    net_tx_bytes = models.BigIntegerField(null=True, blank=True)
    
    # Block I/O
    block_read_bytes = models.BigIntegerField(null=True, blank=True)
    block_write_bytes = models.BigIntegerField(null=True, blank=True)
    
    # PIDs
    pids_count = models.IntegerField(null=True, blank=True)
    
    # Explicit flag to distinguish missing/unreachable readings from zero values
    is_available = models.BooleanField(default=True)
    error_note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['container', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.container.name} @ {self.timestamp}: CPU={self.cpu_percent}%, MEM={self.memory_percent}%"
