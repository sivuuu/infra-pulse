import abc
from typing import List, Dict, Any, Optional

class ContainerRuntimeAdapter(abc.ABC):
    """
    Abstract interface for container runtime operations (Podman / Docker).
    Guarantees least-privilege, normalized data access across runtime implementations.
    """

    @abc.abstractmethod
    def ping(self) -> bool:
        """Check if container runtime is alive and responsive."""
        pass

    @abc.abstractmethod
    def get_runtime_info(self) -> Dict[str, Any]:
        """Return system and runtime version / OS details."""
        pass

    @abc.abstractmethod
    def list_containers(self, all_containers: bool = True) -> List[Dict[str, Any]]:
        """
        List all containers on target runtime.
        Returns normalized list of dictionaries with keys:
          - id, name, image, state, status, created, restart_count, ports, labels, env_keys
        """
        pass

    @abc.abstractmethod
    def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        """
        Fetch resource consumption statistics for a single container.
        Returns normalized dictionary with keys:
          - is_available, cpu_percent, memory_usage_bytes, memory_limit_bytes,
            memory_percent, net_rx_bytes, net_tx_bytes, block_read_bytes, block_write_bytes, pids
        """
        pass

    @abc.abstractmethod
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Fetch resource statistics for all active containers."""
        pass

    @abc.abstractmethod
    def get_container_logs(self, container_id: str, tail: int = 100, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch logs for a given container.
        Returns list of objects with: timestamp, message, source (stdout/stderr)
        """
        pass

    @abc.abstractmethod
    def restart_container(self, container_id: str) -> bool:
        """Administrative action: restart container."""
        pass

    @abc.abstractmethod
    def stop_container(self, container_id: str) -> bool:
        """Administrative action: stop container."""
        pass
