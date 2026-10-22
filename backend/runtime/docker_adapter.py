import subprocess
import json
from typing import List, Dict, Any, Optional
from .base import ContainerRuntimeAdapter
from .podman_adapter import parse_bytes, parse_percent

class DockerAdapter(ContainerRuntimeAdapter):
    """Clean adapter for optional Docker runtime engine."""
    def __init__(self, executable: str = "docker"):
        self.executable = executable

    def _exec(self, args: List[str], timeout: int = 10) -> subprocess.CompletedProcess:
        cmd = [self.executable] + args
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)

    def ping(self) -> bool:
        try:
            res = self._exec(["info", "--format", "{{.ServerVersion}}"], timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def get_runtime_info(self) -> Dict[str, Any]:
        try:
            res = self._exec(["info", "--format", "json"], timeout=5)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                return {
                    "runtime": "docker",
                    "version": data.get("ServerVersion", "unknown"),
                    "os": data.get("OperatingSystem", "linux"),
                    "arch": data.get("Architecture", "unknown"),
                    "cpus": data.get("NCPU", 1),
                    "memory": data.get("MemTotal", 0),
                    "containers_count": data.get("Containers", 0),
                    "status": "healthy"
                }
        except Exception as e:
            return {"runtime": "docker", "status": "unreachable", "error": str(e)}
        return {"runtime": "docker", "status": "unreachable"}

    def list_containers(self, all_containers: bool = True) -> List[Dict[str, Any]]:
        args = ["ps", "--format", "{{json .}}"]
        if all_containers:
            args.append("--all")
        
        try:
            res = self._exec(args, timeout=8)
            if res.returncode != 0:
                raise RuntimeError(f"docker ps error: {res.stderr}")
            
            containers = []
            for line in res.stdout.strip().splitlines():
                if not line.strip():
                    continue
                item = json.loads(line)
                cid = item.get("ID", "")
                name = item.get("Names", cid[:12])
                state = item.get("State", "unknown").lower()
                status = item.get("Status", "")
                
                health = "none"
                if "unhealthy" in status.lower():
                    health = "unhealthy"
                elif "healthy" in status.lower():
                    health = "healthy"

                containers.append({
                    "id": cid,
                    "name": name,
                    "image": item.get("Image", ""),
                    "runtime": "docker",
                    "state": state,
                    "status": status,
                    "health_status": health,
                    "created_at": item.get("CreatedAt"),
                    "restart_count": 0,
                    "ports": [item.get("Ports", "")],
                    "labels": {},
                    "env_keys": [],
                })
            return containers
        except Exception as e:
            raise RuntimeError(f"Failed to query Docker containers: {e}")

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        try:
            res = self._exec(["stats", "--all", "--no-stream", "--format", "{{json .}}"], timeout=8)
            if res.returncode != 0:
                return {}
            
            stats_by_id = {}
            for line in res.stdout.strip().splitlines():
                if not line.strip():
                    continue
                s = json.loads(line)
                cid = s.get("ID", "")
                cpu_p = parse_percent(s.get("CPUPerc"))
                
                mem_str = s.get("MemUsage", "")
                mem_usage, mem_limit = None, None
                if " / " in mem_str:
                    parts = mem_str.split(" / ")
                    mem_usage = parse_bytes(parts[0])
                    mem_limit = parse_bytes(parts[1])
                mem_p = parse_percent(s.get("MemPerc"))

                net_str = s.get("NetIO", "")
                net_rx, net_tx = None, None
                if " / " in net_str:
                    nparts = net_str.split(" / ")
                    net_rx = parse_bytes(nparts[0])
                    net_tx = parse_bytes(nparts[1])

                blk_str = s.get("BlockIO", "")
                blk_r, blk_w = None, None
                if " / " in blk_str:
                    bparts = blk_str.split(" / ")
                    blk_r = parse_bytes(bparts[0])
                    blk_w = parse_bytes(bparts[1])

                try:
                    pids_val = int(s.get("PIDs", 0))
                except Exception:
                    pids_val = None

                stats_by_id[cid] = {
                    "is_available": True,
                    "cpu_percent": cpu_p,
                    "memory_usage_bytes": mem_usage,
                    "memory_limit_bytes": mem_limit,
                    "memory_percent": mem_p,
                    "net_rx_bytes": net_rx,
                    "net_tx_bytes": net_tx,
                    "block_read_bytes": blk_r,
                    "block_write_bytes": blk_w,
                    "pids": pids_val,
                }
            return stats_by_id
        except Exception:
            return {}

    def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        all_stats = self.get_all_stats()
        for cid, stat in all_stats.items():
            if cid.startswith(container_id) or container_id.startswith(cid):
                return stat
        return {
            "is_available": False,
            "cpu_percent": None,
            "memory_usage_bytes": None,
            "memory_limit_bytes": None,
            "memory_percent": None,
            "net_rx_bytes": None,
            "net_tx_bytes": None,
            "block_read_bytes": None,
            "block_write_bytes": None,
            "pids": None,
            "error_note": "Metrics unavailable for container"
        }

    def get_container_logs(self, container_id: str, tail: int = 100, since: Optional[str] = None) -> List[Dict[str, Any]]:
        args = ["logs", "--tail", str(tail), "--timestamps", container_id]
        if since:
            args.extend(["--since", since])
        try:
            res = self._exec(args, timeout=8)
            output = res.stdout + ("\n" + res.stderr if res.stderr else "")
            lines = [l for l in output.splitlines() if l.strip()]
            entries = []
            for line in lines:
                parts = line.split(" ", 1)
                ts_str = parts[0] if len(parts) == 2 else None
                msg = parts[1] if len(parts) == 2 else line
                entries.append({
                    "timestamp": ts_str,
                    "level": "INFO",
                    "source": "docker",
                    "message": msg
                })
            return entries
        except Exception as e:
            return [{"timestamp": None, "level": "ERROR", "source": "collector", "message": str(e)}]

    def restart_container(self, container_id: str) -> bool:
        try:
            res = self._exec(["restart", container_id], timeout=15)
            return res.returncode == 0
        except Exception:
            return False

    def stop_container(self, container_id: str) -> bool:
        try:
            res = self._exec(["stop", container_id], timeout=15)
            return res.returncode == 0
        except Exception:
            return False
