import subprocess
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from .base import ContainerRuntimeAdapter

def parse_bytes(byte_str: str) -> Optional[int]:
    """Parse human readable byte strings (e.g., '12.4MB', '3.1GiB', '500kB', '0B') into integer bytes."""
    if not byte_str or byte_str.strip() == '--':
        return None
    s = byte_str.strip().upper()
    match = re.match(r'^([\d\.]+)\s*([KMGTP]?I?B)?$', s)
    if not match:
        return 0
    val_str, unit = match.groups()
    try:
        val = float(val_str)
    except ValueError:
        return 0

    unit = unit or 'B'
    multipliers = {
        'B': 1,
        'KB': 1000,
        'KIB': 1024,
        'MB': 1000**2,
        'MIB': 1024**2,
        'GB': 1000**3,
        'GIB': 1024**3,
        'TB': 1000**4,
        'TIB': 1024**4,
    }
    return int(val * multipliers.get(unit, 1))

def parse_percent(percent_str: str) -> Optional[float]:
    """Parse percentage strings (e.g. '12.45%') into float."""
    if not percent_str or percent_str.strip() == '--':
        return None
    s = percent_str.strip().replace('%', '')
    try:
        return float(s)
    except ValueError:
        return 0.0


class PodmanAdapter(ContainerRuntimeAdapter):
    def __init__(self, executable: str = "podman"):
        self.executable = executable

    def _exec(self, args: List[str], timeout: int = 10) -> subprocess.CompletedProcess:
        cmd = [self.executable] + args
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )

    def ping(self) -> bool:
        try:
            res = self._exec(["info", "--format", "{{.Host.Distribution.Distribution}}"], timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def get_runtime_info(self) -> Dict[str, Any]:
        try:
            res = self._exec(["info", "--format", "json"], timeout=5)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                host = data.get("host", {})
                version = data.get("version", {})
                return {
                    "runtime": "podman",
                    "version": version.get("Version", "unknown"),
                    "os": host.get("os", "linux"),
                    "arch": host.get("arch", "unknown"),
                    "distribution": host.get("distribution", {}).get("distribution", "linux"),
                    "cpus": host.get("cpus", 1),
                    "memory": host.get("memTotal", 0),
                    "containers_count": host.get("containers", 0),
                    "status": "healthy"
                }
        except Exception as e:
            return {
                "runtime": "podman",
                "status": "unreachable",
                "error": str(e)
            }
        return {"runtime": "podman", "status": "unreachable"}

    def list_containers(self, all_containers: bool = True) -> List[Dict[str, Any]]:
        args = ["ps", "--format", "json"]
        if all_containers:
            args.append("--all")
        
        try:
            res = self._exec(args, timeout=8)
            if res.returncode != 0:
                raise RuntimeError(f"podman ps returned error code {res.returncode}: {res.stderr}")
            
            raw_list = json.loads(res.stdout) if res.stdout.strip() else []
            containers = []
            for item in raw_list:
                cid = item.get("Id", "") or item.get("ID", "")
                names = item.get("Names", [])
                name = names[0] if names else cid[:12]
                state_raw = (item.get("State", "") or "unknown").lower()
                
                # Health status
                status_raw = item.get("Status", "")
                health = "none"
                if "unhealthy" in status_raw.lower():
                    health = "unhealthy"
                elif "healthy" in status_raw.lower():
                    health = "healthy"
                elif state_raw in ("exited", "stopped", "dead"):
                    health = "none"
                
                # Created timestamp
                created_epoch = item.get("Created")
                created_at = None
                if created_epoch:
                    try:
                        created_at = datetime.utcfromtimestamp(created_epoch).isoformat() + "Z"
                    except Exception:
                        created_at = None

                ports = []
                for p in (item.get("Ports") or []):
                    if isinstance(p, dict):
                        host_port = p.get("host_port")
                        cont_port = p.get("container_port")
                        proto = p.get("protocol", "tcp")
                        if host_port and cont_port:
                            ports.append(f"{host_port}:{cont_port}/{proto}")
                        elif cont_port:
                            ports.append(f"{cont_port}/{proto}")

                labels = item.get("Labels") or {}

                containers.append({
                    "id": cid,
                    "name": name,
                    "image": item.get("Image", ""),
                    "runtime": "podman",
                    "state": state_raw,
                    "status": status_raw,
                    "health_status": health,
                    "created_at": created_at,
                    "restart_count": item.get("Restarts", 0),
                    "ports": ports,
                    "labels": labels,
                    "env_keys": [],  # Security: will be populated only from inspect when requested
                })
            return containers
        except Exception as e:
            raise RuntimeError(f"Failed to query Podman containers: {e}")

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Fetch normalized stats for all containers."""
        try:
            res = self._exec(["stats", "--all", "--no-stream", "--format", "json"], timeout=8)
            if res.returncode != 0:
                return {}
            
            raw_list = json.loads(res.stdout) if res.stdout.strip() else []
            stats_by_id = {}
            for s in raw_list:
                cid = s.get("id", "")
                # cpu
                cpu_p = parse_percent(s.get("cpu_percent"))
                # memory "12MB / 1GB"
                mem_str = s.get("mem_usage", "")
                mem_usage = None
                mem_limit = None
                if " / " in mem_str:
                    parts = mem_str.split(" / ")
                    mem_usage = parse_bytes(parts[0])
                    mem_limit = parse_bytes(parts[1])
                mem_p = parse_percent(s.get("mem_percent"))

                # net_io "1.2MB / 3.4MB"
                net_str = s.get("net_io", "")
                net_rx = None
                net_tx = None
                if " / " in net_str:
                    nparts = net_str.split(" / ")
                    net_rx = parse_bytes(nparts[0])
                    net_tx = parse_bytes(nparts[1])

                # block_io "0B / 12KB"
                blk_str = s.get("block_io", "")
                blk_r = None
                blk_w = None
                if " / " in blk_str:
                    bparts = blk_str.split(" / ")
                    blk_r = parse_bytes(bparts[0])
                    blk_w = parse_bytes(bparts[1])

                pids_val = None
                try:
                    pids_val = int(s.get("pids", 0))
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
        # Look up by full id or short prefix
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
            "error_note": "Metrics unavailable for target container"
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
                # Timestamp is usually ISO8601 at start of line
                parts = line.split(" ", 1)
                ts_str = None
                msg = line
                if len(parts) == 2 and (parts[0].startswith("20") and ("T" in parts[0] or "-" in parts[0])):
                    ts_str = parts[0]
                    msg = parts[1]
                
                # Classify log level
                level = "INFO"
                msg_upper = msg.upper()
                if "FATAL" in msg_upper or "PANIC" in msg_upper:
                    level = "FATAL"
                elif "ERROR" in msg_upper or "EXCEPTION" in msg_upper or "FAIL" in msg_upper:
                    level = "ERROR"
                elif "WARN" in msg_upper:
                    level = "WARN"
                elif "DEBUG" in msg_upper or "TRACE" in msg_upper:
                    level = "DEBUG"

                entries.append({
                    "timestamp": ts_str or datetime.utcnow().isoformat() + "Z",
                    "level": level,
                    "source": "podman",
                    "message": msg,
                })
            return entries
        except Exception as e:
            return [{
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": "ERROR",
                "source": "collector",
                "message": f"Log extraction failed: {e}"
            }]

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
