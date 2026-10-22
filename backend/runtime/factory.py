import os
from .base import ContainerRuntimeAdapter
from .podman_adapter import PodmanAdapter
from .docker_adapter import DockerAdapter
from .mock_adapter import MockContainerRuntimeAdapter

def get_runtime_adapter(runtime_type: str = None) -> ContainerRuntimeAdapter:
    """
    Factory function returning the configured runtime adapter.
    Order of precedence:
      1. Explicit argument runtime_type
      2. Environment variable RUNTIME_ADAPTER
      3. Auto-detected availability (Podman -> Docker -> Mock)
    """
    choice = (runtime_type or os.getenv("RUNTIME_ADAPTER", "")).lower()
    
    if choice == "mock":
        return MockContainerRuntimeAdapter()
    elif choice == "docker":
        return DockerAdapter()
    elif choice == "podman":
        return PodmanAdapter()

    # Auto-detection
    podman = PodmanAdapter()
    if podman.ping():
        return podman

    docker = DockerAdapter()
    if docker.ping():
        return docker

    # Fallback default to podman
    return podman
