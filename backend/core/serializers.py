from rest_framework import serializers
from django.contrib.auth.models import User
from .models import AuditLog, UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['role', 'created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_superuser']

    def get_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.role
        return 'admin' if obj.is_superuser else 'operator'

class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = ['id', 'username', 'action', 'target_type', 'target_id', 'details', 'ip_address', 'created_at']

    def get_username(self, obj):
        return obj.user.username if obj.user else 'system'
