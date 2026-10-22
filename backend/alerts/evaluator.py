import re
from datetime import datetime, timezone
from typing import Dict, Any, List
from django.utils import timezone as dj_timezone
from .models import AlertRule, Incident, IncidentStatus, MetricType, ConditionOperator
from containers.models import Container
from metrics.models import MetricSample

def compare_numeric(actual: float, op: str, threshold: float) -> bool:
    if actual is None:
        return False
    if op == ConditionOperator.GT:
        return actual > threshold
    elif op == ConditionOperator.GTE:
        return actual >= threshold
    elif op == ConditionOperator.LT:
        return actual < threshold
    elif op == ConditionOperator.LTE:
        return actual <= threshold
    elif op == ConditionOperator.EQ:
        return abs(actual - threshold) < 1e-6
    elif op == ConditionOperator.NEQ:
        return abs(actual - threshold) >= 1e-6
    return False

def compare_string(actual: str, op: str, expected: str) -> bool:
    actual_s = (actual or "").strip().lower()
    expected_s = (expected or "").strip().lower()
    if op in (ConditionOperator.EQ, ConditionOperator.GTE, ConditionOperator.LTE):
        return actual_s == expected_s
    elif op == ConditionOperator.NEQ:
        return actual_s != expected_s
    return False


class AlertEvaluator:
    """
    Evaluates active AlertRules against current container states and metric samples.
    Implements state transitions: Pending -> Firing -> Resolved,
    with deduplication and alert storm suppression.
    """

    def evaluate_all(self) -> Dict[str, Any]:
        rules = AlertRule.objects.filter(enabled=True)
        containers = Container.objects.all().select_related('target')
        now = dj_timezone.now()

        firing_count = 0
        pending_count = 0
        resolved_count = 0
        evaluated_rules = 0

        # Cache latest metrics per container portably across SQLite & PostgreSQL
        latest_metrics = {}
        for container in containers:
            sample = MetricSample.objects.filter(container=container, is_available=True).order_by('-timestamp').first()
            if sample:
                latest_metrics[container.id] = sample

        for rule in rules:
            evaluated_rules += 1
            # Compile container filter pattern
            pattern = None
            if rule.container_filter and rule.container_filter != '*':
                try:
                    pattern = re.compile(rule.container_filter, re.IGNORECASE)
                except Exception:
                    pattern = None

            for container in containers:
                if pattern and not pattern.search(container.name):
                    continue

                metric_sample = latest_metrics.get(container.id)
                breached, current_value, summary = self._check_rule_breach(rule, container, metric_sample)
                dedup_key = f"{rule.id}:{container.id}"

                active_incident = Incident.objects.filter(
                    dedup_key=dedup_key,
                    status__in=[IncidentStatus.PENDING, IncidentStatus.FIRING]
                ).first()

                if breached:
                    if not active_incident:
                        # New breach -> Pending or Immediate Firing
                        initial_status = IncidentStatus.PENDING
                        if rule.duration_seconds <= 0:
                            initial_status = IncidentStatus.FIRING
                            firing_count += 1
                        else:
                            pending_count += 1

                        Incident.objects.create(
                            rule=rule,
                            container=container,
                            status=initial_status,
                            severity=rule.severity,
                            current_value=current_value,
                            summary=summary,
                            first_seen=now,
                            last_seen=now,
                            dedup_key=dedup_key,
                            storm_count=1
                        )
                    else:
                        # Existing incident -> Deduplicate and check promotion to Firing
                        active_incident.last_seen = now
                        active_incident.current_value = current_value
                        active_incident.storm_count += 1
                        active_incident.summary = summary

                        elapsed = (now - active_incident.first_seen).total_seconds()
                        if active_incident.status == IncidentStatus.PENDING and elapsed >= rule.duration_seconds:
                            active_incident.status = IncidentStatus.FIRING
                            firing_count += 1
                        elif active_incident.status == IncidentStatus.FIRING:
                            firing_count += 1
                        else:
                            pending_count += 1

                        active_incident.save(update_fields=['last_seen', 'current_value', 'storm_count', 'summary', 'status'])

                else:
                    # Metric is within normal parameters -> resolve if previously active
                    if active_incident:
                        active_incident.status = IncidentStatus.RESOLVED
                        active_incident.resolved_at = now
                        active_incident.resolution_note = "Metric normalized within acceptable threshold."
                        active_incident.save(update_fields=['status', 'resolved_at', 'resolution_note'])
                        resolved_count += 1

        return {
            "evaluated_rules": evaluated_rules,
            "firing": firing_count,
            "pending": pending_count,
            "resolved": resolved_count,
            "timestamp": now.isoformat()
        }

    def _check_rule_breach(self, rule: AlertRule, container: Container, sample: MetricSample = None) -> (bool, float, str):
        """Check if a single container breaches a rule."""
        if rule.metric == MetricType.CPU_PERCENT:
            val = sample.cpu_percent if sample else None
            if val is not None and compare_numeric(val, rule.condition, rule.threshold):
                return True, val, f"CPU utilization is {val:.1f}%, exceeding threshold {rule.condition} {rule.threshold}%"
            return False, val, ""

        elif rule.metric == MetricType.MEMORY_PERCENT:
            val = sample.memory_percent if sample else None
            if val is not None and compare_numeric(val, rule.condition, rule.threshold):
                return True, val, f"Memory utilization is {val:.1f}%, exceeding threshold {rule.condition} {rule.threshold}%"
            return False, val, ""

        elif rule.metric == MetricType.HEALTH_STATUS:
            val_str = container.health_status
            target_str = rule.threshold_str or "unhealthy"
            if compare_string(val_str, rule.condition, target_str):
                return True, 1.0, f"Health check status is '{val_str}' (expected {rule.condition} '{target_str}')"
            return False, 0.0, ""

        elif rule.metric == MetricType.STATE:
            val_str = container.state
            target_str = rule.threshold_str or "exited"
            if compare_string(val_str, rule.condition, target_str):
                return True, 1.0, f"Container state is '{val_str}' (rule condition: {rule.condition} '{target_str}')"
            return False, 0.0, ""

        elif rule.metric == MetricType.RESTART_COUNT:
            val = float(container.restart_count)
            if compare_numeric(val, rule.condition, rule.threshold):
                return True, val, f"Restart count reached {container.restart_count}, exceeding threshold {rule.condition} {rule.threshold}"
            return False, val, ""

        elif rule.metric == MetricType.REACHABILITY:
            target_status = container.target.status
            if target_status != 'reachable':
                return True, 0.0, f"Container host target '{container.target.name}' is unreachable ({container.target.error_message})"
            return False, 1.0, ""

        return False, None, ""
