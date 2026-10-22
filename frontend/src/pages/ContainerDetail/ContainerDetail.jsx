import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  Box, 
  ArrowLeft, 
  RotateCw, 
  Square, 
  Cpu, 
  HardDrive, 
  Activity, 
  Terminal, 
  ShieldCheck, 
  AlertTriangle,
  Key,
  Calendar,
  Layers,
  Search,
  Filter
} from 'lucide-react';
import { api } from '../../api/client';
import TimeSeriesChart from '../../components/MetricChart/TimeSeriesChart';
import StatusBadge from '../../components/StatusBadge/StatusBadge';
import { useAuth } from '../../context/AuthContext';

export default function ContainerDetail() {
  const { id } = useParams();
  const { isAdmin } = useAuth();
  const [container, setContainer] = useState(null);
  const [metrics, setMetrics] = useState({ points: [], window: '1h' });
  const [logs, setLogs] = useState([]);
  const [activeWindow, setActiveWindow] = useState('1h');
  const [logFilter, setLogFilter] = useState('');
  const [logLevel, setLogLevel] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState(null);

  const loadData = async () => {
    try {
      const [cData, mData, lData] = await Promise.all([
        api.getContainerDetail(id),
        api.getContainerMetrics(id, activeWindow),
        api.getContainerLogs(id, 100),
      ]);
      setContainer(cData);
      setMetrics(mData);
      setLogs(lData || []);
    } catch (err) {
      console.error('Failed to load container details:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [id, activeWindow]);

  const handleRestart = async () => {
    if (!window.confirm(`Restart container "${container.name}"?`)) return;
    try {
      await api.restartContainer(id);
      setActionMsg({ type: 'success', text: 'Restart signal dispatched.' });
      loadData();
    } catch (e) {
      setActionMsg({ type: 'error', text: e.message });
    }
    setTimeout(() => setActionMsg(null), 4000);
  };

  const handleStop = async () => {
    if (!window.confirm(`Stop container "${container.name}"?`)) return;
    try {
      await api.stopContainer(id);
      setActionMsg({ type: 'success', text: 'Container stopped.' });
      loadData();
    } catch (e) {
      setActionMsg({ type: 'error', text: e.message });
    }
    setTimeout(() => setActionMsg(null), 4000);
  };

  const filteredLogs = logs.filter((l) => {
    const matchesText = !logFilter || l.message.toLowerCase().includes(logFilter.toLowerCase());
    const matchesLevel = !logLevel || l.level.toLowerCase() === logLevel.toLowerCase();
    return matchesText && matchesLevel;
  });

  const timestamps = (metrics.points || []).map((p) => p.timestamp);
  const cpuPoints = (metrics.points || []).map((p) => p.cpu_percent);
  const memPoints = (metrics.points || []).map((p) => p.memory_percent);
  const netRxPoints = (metrics.points || []).map((p) => (p.net_rx_bytes ? Math.round(p.net_rx_bytes / 1024) : 0));
  const netTxPoints = (metrics.points || []).map((p) => (p.net_tx_bytes ? Math.round(p.net_tx_bytes / 1024) : 0));

  if (loading && !container) {
    return <div className="content-body" style={{ color: 'var(--text-muted)' }}>Loading telemetry for container...</div>;
  }

  if (!container) {
    return (
      <div className="content-body">
        <p style={{ color: 'var(--status-critical)' }}>Container not found or telemetry unavailable.</p>
        <Link to="/containers" className="btn btn-secondary btn-sm" style={{ marginTop: '12px', width: 'fit-content' }}>
          <ArrowLeft size={14} /> Back to Containers
        </Link>
      </div>
    );
  }

  return (
    <div className="content-body">
      {/* Back button & Action toast */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Link to="/containers" className="btn btn-secondary btn-sm">
          <ArrowLeft size={14} /> Back to Containers
        </Link>

        {actionMsg && (
          <div
            style={{
              padding: '6px 14px',
              borderRadius: 'var(--radius-md)',
              background: actionMsg.type === 'success' ? 'var(--status-healthy-bg)' : 'var(--status-critical-bg)',
              color: actionMsg.type === 'success' ? 'var(--status-healthy)' : 'var(--status-critical)',
              fontSize: '0.8rem',
              fontWeight: 600,
            }}
          >
            {actionMsg.text}
          </div>
        )}
      </div>

      {/* Hero Header Card */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>{container.name}</h2>
              <StatusBadge state={container.state} health={container.health_status} isStale={container.is_stale} />
              <span className="badge badge-cyan">{container.runtime}</span>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', marginTop: '10px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>Container ID: </span>
                <span className="mono-cell">{container.container_id}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>Image: </span>
                <span style={{ color: 'var(--text-main)' }}>{container.image}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>Host Target: </span>
                <span style={{ color: 'var(--accent-cyan)' }}>{container.target_name}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>Restarts: </span>
                <span style={{ color: container.restart_count > 0 ? 'var(--status-warning)' : 'inherit' }}>
                  {container.restart_count}
                </span>
              </div>
            </div>
          </div>

          {isAdmin && (
            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={handleRestart} className="btn btn-secondary btn-sm" title="Restart container">
                <RotateCw size={14} /> Restart Container
              </button>
              {container.state === 'running' && (
                <button onClick={handleStop} className="btn btn-danger btn-sm" title="Stop container">
                  <Square size={14} /> Stop Container
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Active Incidents Banner if applicable */}
      {container.active_incidents && container.active_incidents.length > 0 && (
        <div 
          style={{
            padding: '16px 20px',
            borderRadius: 'var(--radius-lg)',
            background: 'var(--status-critical-bg)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--status-critical)', fontWeight: 700 }}>
            <AlertTriangle size={18} />
            <span>Active Incidents Correlated With This Service ({container.active_incidents.length})</span>
          </div>
          {container.active_incidents.map((inc) => (
            <div key={inc.id} style={{ fontSize: '0.85rem', color: '#fca5a5' }}>
              • <strong>[{inc.severity.toUpperCase()}] {inc.rule_name}</strong>: {inc.summary}
            </div>
          ))}
        </div>
      )}

      {/* Time-Series Charts with Window Selector */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Activity size={18} style={{ color: 'var(--accent-cyan)' }} />
            <span>Telemetry Charts</span>
          </div>

          <div className="chart-controls">
            {['5m', '15m', '1h', '6h', '24h'].map((w) => (
              <button
                key={w}
                onClick={() => setActiveWindow(w)}
                className={`window-pill ${activeWindow === w ? 'active' : ''}`}
              >
                {w}
              </button>
            ))}
          </div>
        </div>

        <div className="charts-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))' }}>
          <div>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>CPU Utilization (%)</span>
            <div className="chart-wrapper">
              <TimeSeriesChart
                labels={timestamps}
                yAxisLabel="%"
                datasets={[
                  {
                    label: 'CPU %',
                    data: cpuPoints,
                    borderColor: '#00f2fe',
                    backgroundColor: 'rgba(0, 242, 254, 0.12)',
                  },
                ]}
              />
            </div>
          </div>

          <div>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Memory Utilization (%)</span>
            <div className="chart-wrapper">
              <TimeSeriesChart
                labels={timestamps}
                yAxisLabel="%"
                datasets={[
                  {
                    label: 'Memory %',
                    data: memPoints,
                    borderColor: '#818cf8',
                    backgroundColor: 'rgba(129, 140, 248, 0.12)',
                  },
                ]}
              />
            </div>
          </div>

          <div>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Network Traffic (KB)</span>
            <div className="chart-wrapper">
              <TimeSeriesChart
                labels={timestamps}
                yAxisLabel=" KB"
                suggestedMax={500}
                datasets={[
                  {
                    label: 'Net RX (KB)',
                    data: netRxPoints,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.08)',
                  },
                  {
                    label: 'Net TX (KB)',
                    data: netTxPoints,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.08)',
                  },
                ]}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Live Logs Stream */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <Terminal size={18} style={{ color: 'var(--accent-cyan)' }} />
              <span>Container Logs Console</span>
            </div>
            <span className="card-subtitle">
              Sanitized log stream with sensitive token and password redaction
            </span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              placeholder="Search in logs..."
              className="input-field"
              style={{ width: '200px' }}
              value={logFilter}
              onChange={(e) => setLogFilter(e.target.value)}
            />
            <select
              className="select-field"
              value={logLevel}
              onChange={(e) => setLogLevel(e.target.value)}
            >
              <option value="">All Levels</option>
              <option value="INFO">INFO</option>
              <option value="WARN">WARN</option>
              <option value="ERROR">ERROR</option>
              <option value="DEBUG">DEBUG</option>
            </select>
          </div>
        </div>

        <div className="log-terminal">
          {filteredLogs.length === 0 ? (
            <div style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '24px' }}>
              No log lines matching criteria or container output is silent.
            </div>
          ) : (
            filteredLogs.map((l, idx) => (
              <div key={idx} className="log-line">
                <span className="log-ts">{new Date(l.timestamp).toLocaleTimeString()}</span>
                <span className={`log-badge-${l.level}`} style={{ minWidth: '45px', fontWeight: 600 }}>
                  [{l.level}]
                </span>
                <span className="log-msg">
                  {l.message}
                  {l.is_sensitive_redacted && (
                    <span className="redacted-tag">CREDENTIALS REDACTED</span>
                  )}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Metadata & Safe Environment Keys */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Key size={18} style={{ color: 'var(--accent-cyan)' }} />
            <span>Container Metadata & Safe Environment Keys</span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
          <div>
            <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '8px' }}>Labels</h4>
            {container.labels && Object.keys(container.labels).length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {Object.entries(container.labels).map(([k, v]) => (
                  <div key={k} style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', background: 'rgba(255, 255, 255, 0.03)', padding: '4px 8px', borderRadius: '4px' }}>
                    <span style={{ color: 'var(--accent-cyan)' }}>{k}: </span>
                    <span style={{ color: 'var(--text-muted)' }}>{String(v)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>No runtime labels attached.</p>
            )}
          </div>

          <div>
            <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
              Environment Variables (Safe Keys Only)
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {container.env_keys && container.env_keys.length > 0 ? (
                container.env_keys.map((k) => (
                  <span key={k} className="badge badge-cyan" style={{ fontFamily: 'var(--font-mono)' }}>
                    {k}
                  </span>
                ))
              ) : (
                <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Keys sanitized / restricted by host collector policy.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
