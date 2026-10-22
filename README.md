# InfraPulse — Container Observability Platform

[![Backend Tests](https://img.shields.io/badge/pytest-15%20passed-10b981.svg)](#testing)
[![Frontend Build](https://img.shields.io/badge/Vite-built%20in%20565ms-00f2fe.svg)](#frontend)
[![Python](https://img.shields.io/badge/python-3.11-3b82f6.svg)](https://python.org)
[![Podman](https://img.shields.io/badge/runtime-Podman%205.8-8b5cf6.svg)](https://podman.io)
[![Prometheus](https://img.shields.io/badge/metrics-OpenMetrics%20%2Fmetrics-f59e0b.svg)](https://prometheus.io)

**InfraPulse** is a lightweight, secure, locally deployable container observability platform built with Django REST Framework, React (handcrafted Vanilla CSS + Chart.js), and a decoupled runtime collection layer supporting **Podman** (primary) and **Docker** via clean adapter interfaces.

---

## Key Features

1. **Real Data First**:
   - Queries real container telemetry from the local host runtime (`podman ps`, `podman stats`, `podman logs`).
   - If a runtime or data source is unavailable, it is clearly flagged as `UNREACHABLE` or `STOPPED` with error diagnostics (never invented numbers).
   - Distinguishes unavailable metrics (`is_available=False`, displayed as `--`) from actual zero-valued idle readings (`0.0%`).

2. **Decoupled Least-Privilege Architecture**:
   - The public-facing web API and frontend never mount host engine sockets.
   - Telemetry is queried by a restricted host-side collector agent exposing only sanitized, read-only data.

3. **Log Sanitization & Redaction Engine**:
   - Automatic credential scrubbing masks passwords (`password=***REDACTED***`), Bearer tokens, JWTs, AWS access keys, and database connection strings before database ingestion.

4. **Alert State Machine & Storm Prevention**:
   - Configurable rules (CPU, memory, health checks, restart counts, target reachability).
   - State progression: `pending` ➔ `firing` ➔ `resolved`.
   - Deduplication key prevents database alert flooding by tracking consecutive evaluations as `storm_count`.

5. **Prometheus Exposition Endpoint (`/metrics`)**:
   - Standard OpenMetrics endpoint ready for scraping by Prometheus or VictoriaMetrics.

6. **Role-Based Access Control (RBAC) & Audit Trail**:
   - Separate permissions for `Administrator` (manage alert rules, container restart/stop, incident resolution) and `Operator` (read-only telemetry).
   - Immutable audit log records every administrative action.

---

## Technology Stack

- **Backend**: Python 3.11, Django, Django REST Framework, SQLite (default) / PostgreSQL.
- **Frontend**: React 19, React Router v7, Vanilla CSS (dark cyberpunk theme, glassmorphic accents), Chart.js.
- **Metrics**: Prometheus OpenMetrics exposition (`/metrics`).
- **Runtime**: Podman (primary) with clean `ContainerRuntimeAdapter` interface supporting Docker and isolated Mock adapters.
- **Testing**: `pytest`, `pytest-django`.
- **Deployment**: Podman Compose / Docker Compose.

---

## Quick Start (Local Development)

### 1. Prerequisites
Ensure Python 3.11+, Node.js v18+, and Podman 4.0+ are installed.

### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed default users, alert rules, and demo data
python seed_demo_data.py

# Run one-off metrics collection
python manage.py collect_metrics

# Start Django backend server
python manage.py runserver 127.0.0.1:8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open **[http://127.0.0.1:5173](http://127.0.0.1:5173)** in your browser.

### 4. Background Collector Daemon
To continuously collect container stats and evaluate alert rules every 5 seconds:
```bash
cd backend
source venv/bin/activate
python manage.py collect_metrics --daemon --interval 5
```

---

## Default Seed Credentials

| Role | Username | Password | Capabilities |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Full control: create/edit/delete rules, restart/stop containers, resolve incidents |
| **Operator** | `operator` | `operator123` | Read-only inspection of dashboards, telemetry charts, logs, and incidents |

> **Note**: The UI sidebar features a one-click **"Switch to Operator / Admin"** toggle for instant testing of RBAC behavior without re-authenticating.

---

## Automated Test Suite

InfraPulse includes unit and integration tests covering metric normalization, alert state transitions, log redaction, RBAC permissions, and collector handling:

```bash
cd backend
source venv/bin/activate
python -m pytest
```

Output:
```
tests/test_alert_evaluator.py::test_alert_rule_pending_to_firing_transition PASSED
tests/test_alert_evaluator.py::test_alert_recovery_to_resolved PASSED
tests/test_api_endpoints.py::test_health_and_readiness_endpoints PASSED
tests/test_api_endpoints.py::test_metrics_summary_and_prometheus_exposition PASSED
tests/test_api_endpoints.py::test_containers_list_and_filter PASSED
tests/test_integration_collector.py::test_collector_cycle_with_mock_adapter PASSED
tests/test_integration_collector.py::test_collector_unreachable_host_handling PASSED
tests/test_permissions.py::test_admin_vs_operator_permissions PASSED
tests/test_normalization.py::test_parse_bytes_various_units PASSED
tests/test_normalization.py::test_parse_bytes_invalid_or_none PASSED
tests/test_normalization.py::test_parse_percent PASSED
tests/test_scrubber.py::test_scrub_passwords PASSED
tests/test_scrubber.py::test_scrub_bearer_tokens PASSED
tests/test_scrubber.py::test_scrub_database_credentials_in_url PASSED
tests/test_normal_log_untouched PASSED
============================== 15 passed in 0.61s ==============================
```

---

## Directory Structure

```
InfraPulse/
├── backend/
│   ├── manage.py
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── seed_demo_data.py            # Default users, rules, and demo fixtures
│   ├── infrapulse/                  # Django project settings & URL router
│   ├── core/                        # Auth, UserProfile, AuditLog, permissions
│   ├── targets/                     # HostTarget model and views
│   ├── containers/                  # Container inventory, inspect, restart/stop
│   ├── metrics/                     # MetricSample model, time-series, /metrics
│   ├── logs/                        # LogEntry, query console, scrubber
│   ├── alerts/                      # AlertRule, Incident, AlertEvaluator engine
│   ├── runtime/                     # PodmanAdapter, DockerAdapter, MockAdapter
│   ├── collector/                   # Restricted collector agent runner
│   └── tests/                       # Complete pytest test suite
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── api/client.js            # Unified API client
│       ├── context/AuthContext.jsx  # RBAC context & role switching
│       ├── components/              # Sidebar, Topbar, TimeSeriesChart, StatusBadge
│       ├── pages/
│       │   ├── Dashboard/           # Executive KPI overview & trends
│       │   ├── Containers/          # Filterable container inventory
│       │   ├── ContainerDetail/     # Time-series telemetry, logs, metadata
│       │   ├── Alerts/              # Incident stream & Alert Rules builder
│       │   ├── Logs/                # Log investigation console
│       │   ├── Targets/             # Host targets & Prometheus scraper info
│       │   └── Settings/            # Access control & Audit Log
│       └── index.css                # Pure handcrafted Vanilla CSS
├── deploy/
│   ├── Containerfile.backend
│   ├── Containerfile.frontend
│   ├── Containerfile.collector
│   ├── podman-compose.yml
│   └── prometheus.yml
├── docs/
│   ├── ARCHITECTURE.md              # Diagrams, security model, data flow
│   ├── API.md                       # REST API endpoint reference
│   ├── SETUP.md                     # Local & Compose setup instructions
│   └── TROUBLESHOOTING.md           # Diagnostics guide
├── .env.example
└── README.md
```

---

## Security Boundaries, Limitations & Known Gaps

### Security Boundaries
1. **No Socket in Web Application**: The web backend and React frontend are completely isolated from host-level sockets (`/run/podman/podman.sock` or `/var/run/docker.sock`).
2. **Credential Redaction**: Log streams undergo automated regex sanitization for JWT tokens, passwords, database URLs, and AWS access keys before storage.
3. **Environment Variable Sanitization**: Container inspection endpoints only expose environment variable **keys** (names), never runtime secret values.

### Known Gaps & Limitations
1. **Multi-Host Clustering**: While the data model (`HostTarget`) supports multiple remote targets, remote host collection over mutual TLS (mTLS) requires deploying remote collector daemons forwarding telemetry via `/api/logs/ingest/`.
2. **Sampling Granularity**: Default local poll interval is 5 seconds. Sub-second container telemetry spikes may not be captured unless streaming collectors (e.g. eBPF or cgroup v2 watchers) are attached.
3. **Log Retention**: Log storage in local SQLite is bounded to 5,000 entries by default. For production deployments, PostgreSQL with partitioned tables or OpenSearch is recommended.
