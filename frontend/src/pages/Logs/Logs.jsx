import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Terminal, 
  Search, 
  Filter, 
  Download, 
  RefreshCw, 
  ShieldCheck, 
  Box,
  Clock,
  AlertTriangle
} from 'lucide-react';
import { api } from '../../api/client';

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [containers, setContainers] = useState([]);
  const [selectedContainer, setSelectedContainer] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      const params = {};
      if (selectedContainer) params.container_id = selectedContainer;
      if (selectedLevel) params.level = selectedLevel;
      if (searchTerm) params.search = searchTerm;

      const [logData, contData] = await Promise.all([
        api.getLogs(params),
        api.getContainers({ limit: 100 }),
      ]);
      setLogs(logData.results || []);
      setContainers(contData.results || []);
    } catch (err) {
      console.error('Failed to query logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 6000);
    return () => clearInterval(interval);
  }, [selectedContainer, selectedLevel, searchTerm]);

  const handleExport = () => {
    const textData = logs
      .map(
        (l) =>
          `[${l.timestamp}] [${l.level}] (${l.container_name}): ${l.message}`
      )
      .join('\n');
    const blob = new Blob([textData], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `infrapulse_logs_${new Date().toISOString().slice(0, 19)}.txt`;
    a.click();
  };

  return (
    <div className="content-body">
      {/* Search & Filter Toolbar */}
      <div className="card" style={{ padding: '16px 20px' }}>
        <div className="filter-bar" style={{ margin: 0 }}>
          <div className="search-input-wrapper">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="input-field"
              placeholder="Search log messages, stack traces, keywords..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <select
            className="select-field"
            value={selectedContainer}
            onChange={(e) => setSelectedContainer(e.target.value)}
          >
            <option value="">All Containers</option>
            {containers.map((c) => (
              <option key={c.id} value={c.container_id}>
                {c.name} ({c.short_id})
              </option>
            ))}
          </select>

          <select
            className="select-field"
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
          >
            <option value="">All Log Levels</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
            <option value="FATAL">FATAL</option>
            <option value="DEBUG">DEBUG</option>
          </select>

          <button onClick={handleExport} className="btn btn-secondary btn-sm" title="Export logs as text">
            <Download size={14} /> Export Logs
          </button>
        </div>
      </div>

      {/* Log Console Window */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <Terminal size={18} style={{ color: 'var(--accent-cyan)' }} />
              <span>Log Investigation Console</span>
            </div>
            <span className="card-subtitle">
              Showing {logs.length} sanitized log events with automatic credential scrubbing
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            <ShieldCheck size={14} style={{ color: 'var(--status-healthy)' }} />
            <span>Redaction Engine Active</span>
          </div>
        </div>

        <div className="log-terminal" style={{ minHeight: '480px', maxHeight: '680px' }}>
          {logs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-dim)' }}>
              No log records matching filter parameters.
            </div>
          ) : (
            logs.map((l) => (
              <div key={l.id} className="log-line">
                <span className="log-ts">
                  {new Date(l.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
                
                <span className={`log-badge-${l.level}`} style={{ minWidth: '55px', fontWeight: 600 }}>
                  [{l.level}]
                </span>

                <Link
                  to={`/containers/${l.container}`}
                  style={{
                    color: 'var(--accent-cyan)',
                    textDecoration: 'none',
                    fontSize: '0.75rem',
                    background: 'rgba(0, 242, 254, 0.08)',
                    padding: '1px 6px',
                    borderRadius: '3px',
                    flexShrink: 0,
                    marginRight: '6px'
                  }}
                  title={`Container: ${l.container_name}`}
                >
                  {l.container_name}
                </Link>

                <span className="log-msg">
                  {l.message}
                  {l.is_sensitive_redacted && (
                    <span className="redacted-tag">CREDENTIALS REDACTED</span>
                  )}
                  {l.related_incident_id && (
                    <span 
                      style={{ 
                        marginLeft: '8px', 
                        padding: '1px 5px', 
                        background: 'var(--status-critical-bg)', 
                        color: 'var(--status-critical)', 
                        borderRadius: '3px', 
                        fontSize: '0.7rem' 
                      }}
                    >
                      Linked Incident #{l.related_incident_id}
                    </span>
                  )}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
