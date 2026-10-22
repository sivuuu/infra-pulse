import os
import threading
import logging
from datetime import datetime
from django.utils import timezone as dj_timezone
from django.db import transaction
from targets.models import HostTarget, TargetStatus, RuntimeType
from containers.models import Container, ContainerState, ContainerHealth
from metrics.models import MetricSample
from logs.models import LogEntry, LogLevel
from logs.scrubber import sanitize_log_message
from alerts.evaluator import AlertEvaluator
from runtime.factory import get_runtime_adapter

logger = logging.getLogger("infrapulse.collector")
_collection_lock = threading.Lock()

class CollectorRunner:
    def __init__(self, target_name: str = "local-podman-host"):
        self.target_name = target_name
        self.adapter = get_runtime_adapter()
        self.evaluator = AlertEvaluator()

    def run_cycle(self) -> dict:
        """
        Execute one complete collection cycle with least-privilege runtime interrogation.
        Guarantees non-overlapping execution via thread lock.
        """
        if not _collection_lock.acquire(blocking=False):
            logger.warning("Collector cycle already in progress, skipping overlapping run.")
            return {"status": "skipped", "reason": "overlapping_collection"}

        try:
            return self._execute()
        finally:
            _collection_lock.release()

    def _execute(self) -> dict:
        now = dj_timezone.now()
        is_alive = self.adapter.ping()
        info = self.adapter.get_runtime_info() if is_alive else {}

        # 1. Register or update HostTarget
        target, _ = HostTarget.objects.get_or_create(
            name=self.target_name,
            defaults={
                "hostname": os.getenv("HOSTNAME", "localhost"),
                "runtime_type": RuntimeType.PODMAN,
                "status": TargetStatus.REACHABLE if is_alive else TargetStatus.UNREACHABLE,
                "collector_version": "1.0.0",
                "endpoint_url": "restricted-agent://local-socket",
                "metadata": info
            }
        )

        if not is_alive:
            target.status = TargetStatus.UNREACHABLE
            target.error_message = info.get("error", "Container engine unreachable or daemon stopped.")
            target.last_seen = now
            target.save(update_fields=['status', 'error_message', 'last_seen', 'updated_at'])

            # Mark all existing containers for this target as unreachable / stale
            Container.objects.filter(target=target).update(
                health_status=ContainerHealth.UNREACHABLE,
                is_stale=True,
                last_inspected=now
            )

            # Evaluate alerts for reachability
            alert_summary = self.evaluator.evaluate_all()
            return {
                "status": "unreachable",
                "target": target.name,
                "error": target.error_message,
                "alerts": alert_summary,
                "timestamp": now.isoformat()
            }

        # Runtime is alive
        target.status = TargetStatus.REACHABLE
        target.error_message = ""
        target.last_seen = now
        target.metadata = info
        target.save(update_fields=['status', 'error_message', 'last_seen', 'metadata', 'updated_at'])

        # 2. Query containers
        try:
            raw_containers = self.adapter.list_containers(all_containers=True)
        except Exception as e:
            target.status = TargetStatus.DEGRADED
            target.error_message = f"Failed to list containers: {e}"
            target.save(update_fields=['status', 'error_message'])
            return {"status": "degraded", "error": str(e)}

        active_cids = set()
        container_objects = {}

        for rc in raw_containers:
            cid = rc["id"]
            active_cids.add(cid)
            
            # State mapping
            state_val = rc.get("state", "unknown").lower()
            if state_val not in ContainerState.values:
                state_val = ContainerState.UNKNOWN

            health_val = rc.get("health_status", "none").lower()
            if health_val not in ContainerHealth.values:
                health_val = ContainerHealth.NONE

            created_at_dt = None
            if rc.get("created_at"):
                try:
                    created_at_dt = datetime.fromisoformat(rc["created_at"].replace("Z", "+00:00"))
                except Exception:
                    created_at_dt = None

            c_obj, _ = Container.objects.update_or_create(
                target=target,
                container_id=cid,
                defaults={
                    "name": rc.get("name", cid[:12]),
                    "image": rc.get("image", ""),
                    "runtime": rc.get("runtime", "podman"),
                    "state": state_val,
                    "status": rc.get("status", ""),
                    "health_status": health_val,
                    "created_at_runtime": created_at_dt,
                    "restart_count": rc.get("restart_count", 0),
                    "ports": rc.get("ports", []),
                    "labels": rc.get("labels", {}),
                    "is_stale": False,
                    "last_inspected": now,
                }
            )
            container_objects[cid] = c_obj

        # Mark removed containers as stale
        Container.objects.filter(target=target).exclude(container_id__in=active_cids).update(
            is_stale=True,
            last_inspected=now
        )

        # 3. Collect Metrics
        stats_map = self.adapter.get_all_stats()
        metric_samples_created = 0

        for cid, c_obj in container_objects.items():
            # Check stats matching by full ID or prefix
            stat = None
            for s_id, s_data in stats_map.items():
                if cid.startswith(s_id) or s_id.startswith(cid):
                    stat = s_data
                    break

            if stat and stat.get("is_available", True):
                MetricSample.objects.create(
                    container=c_obj,
                    timestamp=now,
                    cpu_percent=stat.get("cpu_percent"),
                    memory_usage_bytes=stat.get("memory_usage_bytes"),
                    memory_limit_bytes=stat.get("memory_limit_bytes"),
                    memory_percent=stat.get("memory_percent"),
                    net_rx_bytes=stat.get("net_rx_bytes"),
                    net_tx_bytes=stat.get("net_tx_bytes"),
                    block_read_bytes=stat.get("block_read_bytes"),
                    block_write_bytes=stat.get("block_write_bytes"),
                    pids_count=stat.get("pids"),
                    is_available=True
                )
                metric_samples_created += 1
            else:
                # Distinguish unavailable metrics from zero-valued metrics
                is_running = c_obj.state == ContainerState.RUNNING
                MetricSample.objects.create(
                    container=c_obj,
                    timestamp=now,
                    cpu_percent=None,
                    memory_usage_bytes=None,
                    memory_limit_bytes=None,
                    memory_percent=None,
                    is_available=False,
                    error_note="Container not running or metrics not provided by runtime"
                )

        # 4. Ingest and sanitize recent logs for active containers
        logs_ingested = 0
        for cid, c_obj in container_objects.items():
            if c_obj.state == ContainerState.RUNNING:
                try:
                    raw_logs = self.adapter.get_container_logs(cid, tail=15)
                    for l in raw_logs:
                        msg = l.get("message", "")
                        sanitized, was_redacted = sanitize_log_message(msg)
                        
                        ts = now
                        if l.get("timestamp"):
                            try:
                                ts = datetime.fromisoformat(l["timestamp"].replace("Z", "+00:00"))
                            except Exception:
                                ts = now

                        # Avoid exact duplicates within the last hour
                        exists = LogEntry.objects.filter(
                            container=c_obj,
                            timestamp=ts,
                            message=sanitized
                        ).exists()

                        if not exists:
                            level = l.get("level", "INFO")
                            if level not in LogLevel.values:
                                level = LogLevel.INFO

                            LogEntry.objects.create(
                                container=c_obj,
                                timestamp=ts,
                                level=level,
                                source=l.get("source", "stdout"),
                                message=sanitized,
                                raw_message="***REDACTED CONTENT***" if was_redacted else sanitized,
                                is_sensitive_redacted=was_redacted
                            )
                            logs_ingested += 1
                except Exception as log_err:
                    logger.debug(f"Could not tail logs for {cid}: {log_err}")

        # 5. Evaluate Alert Rules
        alert_summary = self.evaluator.evaluate_all()

        return {
            "status": "success",
            "target": target.name,
            "containers_monitored": len(container_objects),
            "metrics_collected": metric_samples_created,
            "logs_ingested": logs_ingested,
            "alerts": alert_summary,
            "timestamp": now.isoformat()
        }
