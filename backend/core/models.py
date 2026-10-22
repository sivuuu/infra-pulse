from django.db import models
from django.contrib.auth.models import User

class Role(models.TextChoices):
    ADMIN = 'admin', 'Administrator'
    OPERATOR = 'operator', 'Operator (Read-Only)'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.OPERATOR)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_admin(self):
        return self.role == Role.ADMIN or self.user.is_superuser

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class AuditLog(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_logs')
    action = models.CharField(max_length=64, db_index=True)
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.CharField(max_length=128, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        username = self.user.username if self.user else "system"
        return f"[{self.created_at}] {username} - {self.action} on {self.target_type}:{self.target_id}"
