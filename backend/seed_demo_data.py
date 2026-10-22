import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'infrapulse.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile, Role
from alerts.models import AlertRule, MetricType, ConditionOperator, Severity
from targets.models import HostTarget, TargetStatus, RuntimeType
from containers.models import Container, ContainerState, ContainerHealth
from metrics.models import MetricSample
from logs.models import LogEntry, LogLevel
from django.utils import timezone
from datetime import timedelta

def seed():
    print(">>> Seeding InfraPulse Users & Alert Rules...")

    # 1. Admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@infrapulse.internal', 'is_staff': True, 'is_superuser': True}
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("  Created Admin User: 'admin' (password: 'admin123')")
    UserProfile.objects.update_or_create(user=admin_user, defaults={'role': Role.ADMIN})

    # 2. Operator user (read-only)
    operator_user, created = User.objects.get_or_create(
        username='operator',
        defaults={'email': 'operator@infrapulse.internal', 'is_staff': False, 'is_superuser': False}
    )
    if created:
        operator_user.set_password('operator123')
        operator_user.save()
        print("  Created Operator User: 'operator' (password: 'operator123')")
    UserProfile.objects.update_or_create(user=operator_user, defaults={'role': Role.OPERATOR})

    # 3. Production Alert Rules
    rules = [
        {
            "name": "High CPU Consumption",
            "description": "Fires when container CPU exceeds 80% for over 30 seconds",
            "metric": MetricType.CPU_PERCENT,
            "condition": ConditionOperator.GT,
            "threshold": 80.0,
            "duration_seconds": 30,
            "severity": Severity.WARNING,
            "container_filter": "*"
        },
        {
            "name": "Critical CPU Starvation",
            "description": "Fires when container CPU exceeds 95% for 15 seconds",
            "metric": MetricType.CPU_PERCENT,
            "condition": ConditionOperator.GT,
            "threshold": 95.0,
            "duration_seconds": 15,
            "severity": Severity.CRITICAL,
            "container_filter": "*"
        },
        {
            "name": "High Memory Pressure",
            "description": "Fires when container memory usage exceeds 85% of assigned limit",
            "metric": MetricType.MEMORY_PERCENT,
            "condition": ConditionOperator.GT,
            "threshold": 85.0,
            "duration_seconds": 30,
            "severity": Severity.WARNING,
            "container_filter": "*"
        },
        {
            "name": "Container Health Check Failure",
            "description": "Fires immediately when container runtime health check evaluates to unhealthy",
            "metric": MetricType.HEALTH_STATUS,
            "condition": ConditionOperator.EQ,
            "threshold": 1.0,
            "threshold_str": "unhealthy",
            "duration_seconds": 0,
            "severity": Severity.CRITICAL,
            "container_filter": "*"
        },
        {
            "name": "CrashLoopBackOff / High Restart Count",
            "description": "Fires when container restarts more than 3 times",
            "metric": MetricType.RESTART_COUNT,
            "condition": ConditionOperator.GT,
            "threshold": 3.0,
            "duration_seconds": 0,
            "severity": Severity.WARNING,
            "container_filter": "*"
        },
        {
            "name": "Target Host Unreachable",
            "description": "Fires when collector cannot communicate with host container runtime daemon",
            "metric": MetricType.REACHABILITY,
            "condition": ConditionOperator.EQ,
            "threshold": 0.0,
            "duration_seconds": 0,
            "severity": Severity.CRITICAL,
            "container_filter": "*"
        }
    ]

    for r_data in rules:
        obj, created = AlertRule.objects.get_or_create(
            name=r_data['name'],
            defaults=r_data
        )
        if created:
            print(f"  Created Alert Rule: {obj.name} [{obj.severity}]")

    print(">>> Seeding Demo Fixtures (Explicitly Labeled: '[DEMO]') ...")
    demo_target, _ = HostTarget.objects.get_or_create(
        name="demo-cluster-node-02",
        defaults={
            "hostname": "k8s-worker-02.infrapulse.internal",
            "runtime_type": RuntimeType.PODMAN,
            "status": TargetStatus.REACHABLE,
            "collector_version": "1.0.0",
            "endpoint_url": "agent://demo-worker",
            "last_seen": timezone.now(),
            "metadata": {"demo_flag": True, "os": "linux", "arch": "amd64", "cpus": 8, "memTotal": 16000000000}
        }
    )

    demo_containers = [
        {
            "id": "demo_payment_svc_a1b2",
            "name": "[DEMO] payment-service",
            "image": "registry.corp/payment-service:v2.4",
            "state": ContainerState.RUNNING,
            "status": "Up 4 hours",
            "health": ContainerHealth.HEALTHY,
            "restarts": 0,
            "ports": ["8080:8080/tcp"],
            "cpu": 34.2,
            "mem_pct": 52.8,
            "mem_bytes": 553648128,
        },
        {
            "id": "demo_auth_gateway_c3d4",
            "name": "[DEMO] auth-gateway",
            "image": "registry.corp/envoy-auth:v1.31",
            "state": ContainerState.RUNNING,
            "status": "Up 2 days",
            "health": ContainerHealth.HEALTHY,
            "restarts": 1,
            "ports": ["443:443/tcp"],
            "cpu": 18.5,
            "mem_pct": 28.1,
            "mem_bytes": 294649856,
        },
        {
            "id": "demo_fraud_detector_e5f6",
            "name": "[DEMO] fraud-detection-engine",
            "image": "registry.corp/ml-fraud:latest",
            "state": ContainerState.RUNNING,
            "status": "Up 1 hour (unhealthy)",
            "health": ContainerHealth.UNHEALTHY,
            "restarts": 4,
            "ports": ["9090:9090/tcp"],
            "cpu": 91.4,
            "mem_pct": 89.2,
            "mem_bytes": 1932735283,
        }
    ]

    now = timezone.now()
    for dc in demo_containers:
        c, _ = Container.objects.update_or_create(
            target=demo_target,
            container_id=dc["id"],
            defaults={
                "name": dc["name"],
                "image": dc["image"],
                "runtime": "podman",
                "state": dc["state"],
                "status": dc["status"],
                "health_status": dc["health"],
                "created_at_runtime": now - timedelta(hours=4),
                "restart_count": dc["restarts"],
                "ports": dc["ports"],
                "labels": {"is_demo_data": "true", "environment": "staging"},
                "env_keys": ["PORT", "ENVIRONMENT", "WORKER_POOL_SIZE"],
                "is_stale": False,
                "last_inspected": now
            }
        )

        # Generate 15 time-series points
        for i in range(15):
            point_time = now - timedelta(minutes=(15 - i) * 2)
            noise = (i % 3) * 1.5
            MetricSample.objects.create(
                container=c,
                timestamp=point_time,
                cpu_percent=max(0.0, round(dc["cpu"] + noise - 2.0, 1)),
                memory_usage_bytes=dc["mem_bytes"],
                memory_limit_bytes=2147483648,
                memory_percent=round(dc["mem_pct"] + (i % 2) * 0.5, 1),
                net_rx_bytes=1024000 * (i + 1),
                net_tx_bytes=2048000 * (i + 1),
                block_read_bytes=512000,
                block_write_bytes=1024000,
                pids_count=18,
                is_available=True
            )

        # Sample logs
        LogEntry.objects.create(
            container=c,
            timestamp=now - timedelta(minutes=5),
            level=LogLevel.INFO,
            source="stdout",
            message=f"[{c.name}] Health probe responded HTTP 200 OK across cluster.",
            raw_message=f"[{c.name}] Health probe responded HTTP 200 OK across cluster."
        )
        if dc["health"] == ContainerHealth.UNHEALTHY:
            LogEntry.objects.create(
                container=c,
                timestamp=now - timedelta(minutes=2),
                level=LogLevel.ERROR,
                source="stderr",
                message=f"[{c.name}] Memory threshold reached 89.2%! GC latency spike 420ms. Token=***REDACTED_JWT***",
                raw_message=f"[{c.name}] Memory threshold reached 89.2%! GC latency spike 420ms. Token=eyJhbGciOi...",
                is_sensitive_redacted=True
            )

    print(">>> Seed completed successfully!")

if __name__ == '__main__':
    seed()
