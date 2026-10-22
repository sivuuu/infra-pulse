const API_BASE = '/api';

export async function fetchJson(endpoint, options = {}) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    let errorMsg = `HTTP Error ${res.status}`;
    try {
      const errJson = await res.json();
      errorMsg = errJson.error || errJson.message || JSON.stringify(errJson);
    } catch (_) {}
    throw new Error(errorMsg);
  }

  return res.json();
}

export const api = {
  // Health
  getHealth: () => fetchJson('/health/'),
  getReadiness: () => fetchJson('/ready/'),

  // Auth & Roles
  getMe: () => fetchJson('/auth/me/'),
  login: (username, password) =>
    fetchJson('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  logout: () => fetchJson('/auth/logout/', { method: 'POST' }),

  // Summary & Metrics
  getSummary: () => fetchJson('/metrics/summary/'),
  getTimeSeries: (window = '1h') => fetchJson(`/metrics/time-series/?window=${window}`),

  // Targets
  getTargets: () => fetchJson('/targets/'),

  // Containers
  getContainers: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return fetchJson(`/containers/${q ? `?${q}` : ''}`);
  },
  getContainerDetail: (id) => fetchJson(`/containers/${id}/`),
  getContainerMetrics: (id, window = '1h') =>
    fetchJson(`/containers/${id}/metrics/?window=${window}`),
  getContainerLogs: (id, limit = 100) =>
    fetchJson(`/containers/${id}/logs/?limit=${limit}`),
  restartContainer: (id) =>
    fetchJson(`/containers/${id}/restart/`, { method: 'POST' }),
  stopContainer: (id) =>
    fetchJson(`/containers/${id}/stop/`, { method: 'POST' }),

  // Logs Explorer
  getLogs: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return fetchJson(`/logs/${q ? `?${q}` : ''}`);
  },

  // Alerts & Incidents
  getAlertRules: () => fetchJson('/alerts/rules/'),
  createAlertRule: (rule) =>
    fetchJson('/alerts/rules/', {
      method: 'POST',
      body: JSON.stringify(rule),
    }),
  updateAlertRule: (id, rule) =>
    fetchJson(`/alerts/rules/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(rule),
    }),
  deleteAlertRule: (id) =>
    fetchJson(`/alerts/rules/${id}/`, { method: 'DELETE' }),

  getIncidents: (status = 'all', severity = '') => {
    const p = new URLSearchParams();
    if (status && status !== 'all') p.set('status', status);
    if (severity) p.set('severity', severity);
    return fetchJson(`/alerts/incidents/?${p.toString()}`);
  },
  resolveIncident: (id, note = '') =>
    fetchJson(`/alerts/incidents/${id}/resolve/`, {
      method: 'POST',
      body: JSON.stringify({ note }),
    }),
  evaluateAlerts: () =>
    fetchJson('/alerts/incidents/evaluate/', { method: 'POST' }),

  // Collector
  triggerCollector: () =>
    fetchJson('/collector/trigger/', { method: 'POST' }),

  // Audit Logs
  getAuditLogs: () => fetchJson('/audit-logs/'),
};
