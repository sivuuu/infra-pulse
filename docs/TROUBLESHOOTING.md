# InfraPulse Troubleshooting Guide

## 1. Container Runtime Unreachable
### Symptoms
- Dashboard topbar shows `Runtime Unreachable` (red pill).
- Target status in `/targets` is marked `UNREACHABLE`.
- Containers display `Stale Target` or `Unreachable`.

### Resolution Steps
1. Verify if Podman virtual machine is running (macOS / Windows):
   ```bash
   podman machine list
   podman machine start
   ```
2. Check if Podman CLI is responsive:
   ```bash
   podman info
   ```
3. If using Docker instead of Podman, set the environment variable:
   ```bash
   export RUNTIME_ADAPTER=docker
   ```
4. In test environments without a container runtime, set:
   ```bash
   export RUNTIME_ADAPTER=mock
   ```

---

## 2. Missing Metrics vs Zero Values
### Explanation
InfraPulse explicitly avoids inventing telemetry numbers:
- If a container is **stopped or exited**, `is_available` is set to `False`. The UI displays `--` instead of `0%`.
- If a container is **running and idle**, `is_available` is `True` and CPU reads `0.0%`.
- If metrics fail to be collected for a container, check `error_note` on the `MetricSample`.

---

## 3. Alert Storms & Deduplication
### How InfraPulse Handles It
- When a threshold is breached consecutively across hundreds of evaluations, InfraPulse does NOT spam rows.
- It increments `storm_count` on the active incident and updates `last_seen`.
- If you notice unexpected alert firings, verify the rule's `duration_seconds`:
  - `duration_seconds: 0` fires immediately on first breach.
  - `duration_seconds: 30` requires the breach to persist for at least 30 seconds before transitioning from `pending` to `firing`.

---

## 4. RBAC Permission Denied (403 Forbidden)
### Cause
Attempting to create alert rules, restart/stop containers, or resolve incidents while authenticated as a read-only Operator.
### Resolution
- In the UI sidebar, click **"Switch to Admin"** (or in Settings).
- Use admin credentials: username `admin`, password `admin123`.
