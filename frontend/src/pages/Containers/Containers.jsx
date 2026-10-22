import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Box, 
  Search, 
  RotateCw, 
  Square, 
  ExternalLink, 
  Layers,
  Filter,
  Check,
  AlertCircle
} from 'lucide-react';
import { api } from '../../api/client';
import StatusBadge from '../../components/StatusBadge/StatusBadge';
import { useAuth } from '../../context/AuthContext';

export default function Containers() {
  const { isAdmin } = useAuth();
  const [containers, setContainers] = useState([]);
  const [targets, setTargets] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedState, setSelectedState] = useState('');
  const [selectedHealth, setSelectedHealth] = useState('');
  const [selectedTarget, setSelectedTarget] = useState('');
  const [selectedRuntime, setSelectedRuntime] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState(null);

  const fetchContainers = async () => {
    try {
      const params = {};
      if (search) params.search = search;
      if (selectedState) params.state = selectedState;
      if (selectedHealth) params.health = selectedHealth;
      if (selectedTarget) params.target = selectedTarget;
      if (selectedRuntime) params.runtime = selectedRuntime;

      const [cData, tData] = await Promise.all([
        api.getContainers(params),
        api.getTargets()
      ]);
      setContainers(cData.results || []);
      setTargets(tData.results || []);
    } catch (err) {
      console.error('Failed to fetch containers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContainers();
    const interval = setInterval(fetchContainers, 6000);
    return () => clearInterval(interval);
  }, [search, selectedState, selectedHealth, selectedTarget, selectedRuntime]);

  const handleRestart = async (id, name) => {
    if (!window.confirm(`Are you sure you want to restart container "${name}"?`)) return;
    try {
      await api.restartContainer(id);
      setActionMessage({ type: 'success', text: `Container "${name}" restart signal dispatched.` });
      fetchContainers();
    } catch (err) {
      setActionMessage({ type: 'error', text: `Failed to restart: ${err.message}` });
    }
    setTimeout(() => setActionMessage(null), 4000);
  };

  const handleStop = async (id, name) => {
    if (!window.confirm(`Are you sure you want to stop container "${name}"?`)) return;
    try {
      await api.stopContainer(id);
      setActionMessage({ type: 'success', text: `Container "${name}" stopped.` });
      fetchContainers();
    } catch (err) {
      setActionMessage({ type: 'error', text: `Failed to stop: ${err.message}` });
    }
    setTimeout(() => setActionMessage(null), 4000);
  };

  return (
    <div className="content-body">
      {actionMessage && (
        <div 
          style={{ 
            padding: '12px 16px', 
            borderRadius: 'var(--radius-md)',
            background: actionMessage.type === 'success' ? 'var(--status-healthy-bg)' : 'var(--status-critical-bg)',
            border: `1px solid ${actionMessage.type === 'success' ? 'var(--status-healthy)' : 'var(--status-critical)'}`,
            color: actionMessage.type === 'success' ? 'var(--status-healthy)' : 'var(--status-critical)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '0.85rem',
            fontWeight: 600
          }}
        >
          {actionMessage.type === 'success' ? <Check size={18} /> : <AlertCircle size={18} />}
          <span>{actionMessage.text}</span>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="card" style={{ padding: '16px 20px' }}>
        <div className="filter-bar" style={{ margin: 0 }}>
          <div className="search-input-wrapper">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="input-field"
              placeholder="Search containers by name, container ID, or image..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            className="select-field"
            value={selectedState}
            onChange={(e) => setSelectedState(e.target.value)}
          >
            <option value="">All States</option>
            <option value="running">Running</option>
            <option value="exited">Exited</option>
            <option value="stopped">Stopped</option>
            <option value="paused">Paused</option>
          </select>

          <select
            className="select-field"
            value={selectedHealth}
            onChange={(e) => setSelectedHealth(e.target.value)}
          >
            <option value="">All Health Statuses</option>
            <option value="healthy">Healthy</option>
            <option value="unhealthy">Unhealthy</option>
            <option value="unreachable">Unreachable</option>
            <option value="none">No Probe Configured</option>
          </select>

          <select
            className="select-field"
            value={selectedRuntime}
            onChange={(e) => setSelectedRuntime(e.target.value)}
          >
            <option value="">All Runtimes</option>
            <option value="podman">Podman</option>
            <option value="docker">Docker</option>
          </select>

          <select
            className="select-field"
            value={selectedTarget}
            onChange={(e) => setSelectedTarget(e.target.value)}
          >
            <option value="">All Host Targets</option>
            {targets.map((t) => (
              <option key={t.id} value={t.name}>
                {t.name} ({t.status})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Containers Fleet Inventory Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <Box size={18} style={{ color: 'var(--accent-cyan)' }} />
              <span>Container Inventory</span>
            </div>
            <span className="card-subtitle">
              Showing {containers.length} active monitoring targets across connected engines
            </span>
          </div>
        </div>

        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Container Name & ID</th>
                <th>Status</th>
                <th>Target Host</th>
                <th>Image</th>
                <th>Ports</th>
                <th>Restarts</th>
                <th>Live CPU / Mem</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {containers.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-dim)' }}>
                    No containers matching filter criteria.
                  </td>
                </tr>
              ) : (
                containers.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <Link
                        to={`/containers/${c.id}`}
                        style={{ color: 'var(--text-main)', textDecoration: 'none', fontWeight: 600 }}
                      >
                        {c.name}
                      </Link>
                      <div className="mono-cell" style={{ color: 'var(--text-dim)', fontSize: '0.72rem' }}>
                        ID: {c.short_id} • Runtime: {c.runtime}
                      </div>
                    </td>

                    <td>
                      <StatusBadge state={c.state} health={c.health_status} isStale={c.is_stale} />
                    </td>

                    <td>
                      <div style={{ fontSize: '0.85rem', fontWeight: 500 }}>{c.target_name}</div>
                      <div style={{ fontSize: '0.7rem', color: c.target_status === 'reachable' ? 'var(--status-healthy)' : 'var(--status-critical)' }}>
                        {c.target_status}
                      </div>
                    </td>

                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={c.image}>
                      {c.image}
                    </td>

                    <td style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                      {(c.ports && c.ports.length > 0) ? c.ports.join(', ') : 'None'}
                    </td>

                    <td className="mono-cell" style={{ color: c.restart_count > 3 ? 'var(--status-warning)' : 'var(--text-main)' }}>
                      {c.restart_count}
                    </td>

                    <td className="mono-cell" style={{ minWidth: '130px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                          <span style={{ color: 'var(--text-dim)' }}>CPU:</span>
                          <span style={{ color: c.cpu_percent > 80 ? 'var(--status-critical)' : 'var(--accent-cyan)' }}>
                            {c.cpu_percent !== null && c.cpu_percent !== undefined ? `${c.cpu_percent.toFixed(1)}%` : '--'}
                          </span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                          <span style={{ color: 'var(--text-dim)' }}>Mem:</span>
                          <span>
                            {c.memory_percent !== null && c.memory_percent !== undefined ? `${c.memory_percent.toFixed(1)}%` : '--'}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Link to={`/containers/${c.id}`} className="btn btn-secondary btn-sm" title="Detailed Telemetry">
                          Inspect
                        </Link>

                        {isAdmin && (
                          <>
                            <button
                              onClick={() => handleRestart(c.id, c.name)}
                              className="btn btn-secondary btn-sm"
                              title="Restart container via runtime engine"
                            >
                              <RotateCw size={12} />
                            </button>

                            {c.state === 'running' && (
                              <button
                                onClick={() => handleStop(c.id, c.name)}
                                className="btn btn-danger btn-sm"
                                title="Stop container"
                              >
                                <Square size={12} />
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
