import pytest
from datetime import timedelta
from django.utils import timezone
from alerts.models import AlertRule, Incident, IncidentStatus, MetricType, ConditionOperator, Severity
from alerts.evaluator import AlertEvaluator
from targets.models import HostTarget, TargetStatus
from containers.models import Container, ContainerState, ContainerHealth
from metrics.models import MetricSample

@pytest.mark.django_db
def test_alert_rule_pending_to_firing_transition():
    target = HostTarget.objects.create(name="test-target", status=TargetStatus.REACHABLE)
    container = Container.objects.create(
        target=target,
        container_id="test_cont_cpu",
        name="cpu-hog",
        state=ContainerState.RUNNING,
        health_status=ContainerHealth.HEALTHY
    )

    rule = AlertRule.objects.create(
        name="Test High CPU",
        metric=MetricType.CPU_PERCENT,
        condition=ConditionOperator.GT,
        threshold=80.0,
        duration_seconds=30,  # Requires 30 seconds before firing
        severity=Severity.WARNING
    )

    now = timezone.now()
    # Create sample exceeding threshold
    MetricSample.objects.create(
        container=container,
        timestamp=now,
        cpu_percent=89.5,
        is_available=True
    )

    evaluator = AlertEvaluator()
    summary = evaluator.evaluate_all()

    # First breach with duration > 0 must be PENDING
    assert summary['pending'] == 1
    assert summary['firing'] == 0

    incident = Incident.objects.get(rule=rule, container=container)
    assert incident.status == IncidentStatus.PENDING
    assert incident.storm_count == 1

    # Simulate subsequent breach after 35 seconds (exceeding 30s duration)
    incident.first_seen = now - timedelta(seconds=35)
    incident.save(update_fields=['first_seen'])

    summary2 = evaluator.evaluate_all()
    incident.refresh_from_db()

    # Should transition to FIRING
    assert incident.status == IncidentStatus.FIRING
    assert incident.storm_count == 2
    assert summary2['firing'] == 1

@pytest.mark.django_db
def test_alert_recovery_to_resolved():
    target = HostTarget.objects.create(name="test-target-2", status=TargetStatus.REACHABLE)
    container = Container.objects.create(
        target=target,
        container_id="test_cont_mem",
        name="mem-hog",
        state=ContainerState.RUNNING,
        health_status=ContainerHealth.HEALTHY
    )

    rule = AlertRule.objects.create(
        name="Test Memory Pressure",
        metric=MetricType.MEMORY_PERCENT,
        condition=ConditionOperator.GT,
        threshold=80.0,
        duration_seconds=0,  # Immediate firing
        severity=Severity.CRITICAL
    )

    now = timezone.now()
    # Breach
    MetricSample.objects.create(
        container=container,
        timestamp=now,
        memory_percent=85.0,
        is_available=True
    )

    evaluator = AlertEvaluator()
    evaluator.evaluate_all()

    incident = Incident.objects.get(rule=rule, container=container)
    assert incident.status == IncidentStatus.FIRING

    # Now metric normalizes to 40%
    MetricSample.objects.create(
        container=container,
        timestamp=now + timedelta(seconds=10),
        memory_percent=40.0,
        is_available=True
    )

    summary_recovered = evaluator.evaluate_all()
    incident.refresh_from_db()

    # Must transition to RESOLVED
    assert incident.status == IncidentStatus.RESOLVED
    assert incident.resolved_at is not None
    assert summary_recovered['resolved'] == 1
