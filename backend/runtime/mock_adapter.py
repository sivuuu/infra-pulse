from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import ContainerRuntimeAdapter

class MockContainerRuntimeAdapter(ContainerRuntimeAdapter):
    """
    Mock adapter with deterministic telemetry for testing edge cases,
    unreachable hosts, alert evaluation, and metric normalization without external dependencies.
    """
    def __init__(self, is_alive: bool = True):
        self.is_alive = is_alive
        self.containers = [
            {
                "id": "mock_nginx_01",
                "name": "web-gateway",
                "image": "nginx:alpine",
                "runtime": "podman",
                "state": "running",
                "status": "Up 2 hours",
                "health_status": "healthy",
                "created_at": "2026-10-22T10:00:00Z",
                "restart_count": 0,
                "ports": ["80:80/tcp", "443:443/tcp"],
                "labels": {"tier": "frontend", "service": "gateway"},
                "env_keys": ["PORT", "WORKERS"],
            },
            {
                "id": "mock_db_02",
                "name": "primary-postgres",
                "image": "postgres:16-alpine",
                "runtime": "podman",
                "state": "running",
                "status": "Up 3 hours (unhealthy)",
                "health_status": "unhealthy",
                "created_at": "2026-10-22T09:00:00Z",
                "restart_count": 3,
                "ports": ["5432:5432/tcp"],
                "labels": {"tier": "database", "service": "postgres"},
                "env_keys": ["POSTGRES_DB", "POSTGRES_USER"],
            },
            {
                "id": "mock_worker_03",
                "name": "task-worker",
                "image": "worker:v1",
                "runtime": "podman",
                "state": "exited",
                "status": "Exited (137) 10 minutes ago",
                "health_status": "none",
                "created_at": "2026-10-22T08:00:00Z",
                "restart_count": 5,
                "ports": [],
                "labels": {"tier": "worker"},
                "env_keys": ["CONCURRENCY"],
            }
        ]
        self.stats = {
            "mock_nginx_01": {
                "is_available": True,
                "cpu_percent": 14.5,
                "memory_usage_bytes": 128 * 1024 * 1024,
                "memory_limit_bytes": 1024 * 1024 * 1024,
                "memory_percent": 12.5,
                "net_rx_bytes": 2048500,
                "net_tx_bytes": 8392100,
                "block_read_bytes": 10240,
                "block_write_bytes": 40960,
                "pids": 12
            },
            "mock_db_02": {
                "is_available": True,
                "cpu_percent": 88.2,  # Spike to test alert triggering!
                "memory_usage_bytes": 950 * 1024 * 1024,
                "memory_limit_bytes": 1024 * 1024 * 1024,
                "memory_percent": 92.7,
                "net_rx_bytes": 1400200,
                "net_tx_bytes": 1800400,
                "block_read_bytes": 52428800,
                "block_write_bytes": 104857600,
                "pids": 45
            },
            "mock_worker_03": {
                "is_available": False,  # Missing metrics due to exited state
                "cpu_percent": None,
                "memory_usage_bytes": None,
                "memory_limit_bytes": None,
                "memory_percent": None,
                "net_rx_bytes": None,
                "net_tx_bytes": None,
                "block_read_bytes": None,
                "block_write_bytes": None,
                "pids": None,
                "error_note": "Container is exited"
            }
        }

    def ping(self) -> bool:
        return self.is_alive

    def get_runtime_info(self) -> Dict[str, Any]:
        if not self.is_alive:
            return {"runtime": "mock", "status": "unreachable", "error": "Connection refused"}
        return {
            "runtime": "mock",
            "version": "1.0.0-mock",
            "os": "linux",
            "arch": "arm64",
            "distribution": "fedora",
            "cpus": 4,
            "memory": 8589934592,
            "containers_count": len(self.containers),
            "status": "healthy"
        }

    def list_containers(self, all_containers: bool = True) -> List[Dict[str, Any]]:
        if not self.is_alive:
            raise RuntimeError("Cannot connect to container runtime: connection refused")
        return self.containers

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        if not self.is_alive:
            return {}
        return self.stats

    def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        if not self.is_alive:
            return {"is_available": False, "error_note": "Runtime unreachable"}
        return self.stats.get(container_id, {
            "is_available": False,
            "error_note": f"Container {container_id} not found"
        })

    def get_container_logs(self, container_id: str, tail: int = 100, since: Optional[str] = None) -> List[Dict[str, Any]]:
        return [
            {"timestamp": "2026-10-22T10:15:00Z", "level": "INFO", "source": "stdout", "message": "Service initialized worker pool size 8"},
            {"timestamp": "2026-10-22T10:15:30Z", "level": "WARN", "source": "stderr", "message": "Connection latency high: 142ms to upstream"},
            {"timestamp": "2026-10-22T10:16:00Z", "level": "ERROR", "source": "stderr", "message": "Failed query lock acquisition timeout"},
        ]

    def restart_container(self, container_id: str) -> bool:
        for c in self.containers:
            if c["id"] == container_id:
                c["state"] = "running"
                c["status"] = "Up 1 second"
                c["restart_count"] += 1
                return True
        return False

    def stop_container(self, container_id: str) -> bool:
        for c in self.containers:
            if c["id"] == container_id:
                c["state"] = "stopped"
                c["status"] = "Exited (0) Just now"
                return True
        return False
