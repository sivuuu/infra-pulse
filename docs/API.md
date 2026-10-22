# InfraPulse REST API Documentation

Base URI: `/api/`

---

## 1. System Health & Readiness

### `GET /api/health/`
Checks database connectivity, collector registration, and engine status.
- **Response**: `200 OK` (or `503 Service Unavailable` if degraded)
```json
{
  "status": "healthy",
  "database": "connected",
  "targets_count": 2,
  "containers_count": 23,
  "version": "1.0.0"
}
```

### `GET /api/ready/`
Kubernetes/Compose readiness probe.
- **Response**: `200 OK` -> `{"status": "ready"}`

---

## 2. Metrics & Observability

### `GET /api/metrics/summary/`
Executive dashboard summary metrics across the fleet.
- **Response**:
```json
{
  "containers": {
    "total": 23,
    "running": 3,
    "stopped": 18,
    "healthy": 2,
    "unhealthy": 1,
    "unreachable": 1
  },
  "system_metrics": {
    "average_cpu_percent": 49.03,
    "average_memory_percent": 56.7,
    "total_memory_usage_bytes": 2781033267,
    "total_net_rx_bytes": 46080000,
    "total_net_tx_bytes": 92160000
  },
  "alerts": {
    "firing": 2,
    "pending": 2,
    "critical": 1
  },
  "collector": {
    "status": "healthy",
    "targets_count": 2,
    "last_collection": "2026-10-22T16:56:46Z",
    "freshness_seconds": 4
  }
}
```

### `GET /api/metrics/time-series/?window=1h`
Time-series points for historical trend graphs.
- **Parameters**: `window` (`5m`, `15m`, `1h`, `6h`, `24h`)

### `GET /metrics`
Prometheus standard exposition endpoint for Prometheus / VictoriaMetrics scraping.

---

## 3. Containers Inventory

### `GET /api/containers/`
List monitored containers.
- **Query Parameters**:
  - `search`: Filter by name, ID, or image
  - `state`: `running`, `exited`, `stopped`, `paused`
  - `health`: `healthy`, `unhealthy`, `unreachable`, `none`
  - `runtime`: `podman`, `docker`
  - `target`: Filter by host target name

### `GET /api/containers/<id>/`
Retrieve detailed telemetry for a single container.

### `GET /api/containers/<id>/metrics/?window=1h`
Container-specific CPU, Memory, Network RX/TX, Block I/O time-series points.

### `GET /api/containers/<id>/logs/?limit=100`
Retrieve recent sanitized logs for this container.

### `POST /api/containers/<id>/restart/` *(Admin Only)*
Dispatches container restart signal through runtime adapter. Records audit log.

### `POST /api/containers/<id>/stop/` *(Admin Only)*
Dispatches container stop signal through runtime adapter. Records audit log.

---

## 4. Alerts & Incidents

### `GET /api/alerts/rules/`
List configured alert evaluation rules.

### `POST /api/alerts/rules/` *(Admin Only)*
Create a new alert rule.
```json
{
  "name": "High CPU Spike",
  "metric": "cpu_percent",
  "condition": ">",
  "threshold": 85.0,
  "duration_seconds": 30,
  "severity": "warning",
  "container_filter": "*"
}
```

### `GET /api/alerts/incidents/`
Query incidents timeline.
- **Query Parameters**:
  - `status`: `all`, `firing`, `pending`, `resolved`
  - `severity`: `critical`, `warning`, `info`
  - `container`: Container ID or name

### `POST /api/alerts/incidents/<id>/resolve/` *(Admin Only)*
Mark an active incident as resolved with custom resolution note.
```json
{
  "note": "Root cause mitigated; pod memory quota increased."
}
```

---

## 5. Logs Explorer

### `GET /api/logs/`
Query logs across all containers.
- **Query Parameters**:
  - `search`: Full text keyword filter
  - `container_id`: Target container
  - `level`: `INFO`, `WARN`, `ERROR`, `FATAL`, `DEBUG`
  - `incident_id`: Linked incident ID

---

## 6. Access Control & Audit

### `POST /api/auth/login/`
Authenticate credentials.
- **Request**: `{"username": "admin", "password": "admin123"}`

### `GET /api/audit-logs/`
Read-only trail of all administrative actions.
