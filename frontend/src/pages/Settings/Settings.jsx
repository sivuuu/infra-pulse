import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  UserCheck, 
  FileText, 
  Lock, 
  Database, 
  Terminal, 
  Key,
  Clock,
  Layers
} from 'lucide-react';
import { api } from '../../api/client';
import { useAuth } from '../../context/AuthContext';

export default function Settings() {
  const { user, isAdmin, switchRole } = useAuth();
  const [auditLogs, setAuditLogs] = useState([]);
  const [healthInfo, setHealthInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAuditLogs = async () => {
    try {
      const [logData, hData] = await Promise.all([
        api.getAuditLogs(),
        api.getHealth()
      ]);
      setAuditLogs(logData.results || []);
      setHealthInfo(hData);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
    const interval = setInterval(fetchAuditLogs, 6000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="content-body">
      {/* Access Control & RBAC Card */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <ShieldCheck size={18} style={{ color: 'var(--accent-cyan)' }} />
              <span>Role-Based Access Control (RBAC)</span>
            </div>
            <span className="card-subtitle">
              Current authenticated session and role privileges
            </span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => switchRole('admin')}
              className={`btn btn-sm ${isAdmin ? 'btn-primary' : 'btn-secondary'}`}
            >
              Simulate Administrator
            </button>
            <button
              onClick={() => switchRole('operator')}
              className={`btn btn-sm ${!isAdmin ? 'btn-primary' : 'btn-secondary'}`}
            >
              Simulate Operator (Read-Only)
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
          <div style={{ padding: '16px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '6px' }}>Current User</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{user?.username}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Role: <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{user?.role?.toUpperCase()}</span></div>
          </div>

          <div style={{ padding: '16px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '6px' }}>Administrative Permissions</div>
            <div style={{ fontSize: '0.85rem', color: isAdmin ? 'var(--status-healthy)' : 'var(--status-warning)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
              <span className={`badge ${isAdmin ? 'badge-healthy' : 'badge-warning'}`}>
                {isAdmin ? 'FULL ACCESS (Admin)' : 'READ-ONLY (Operator)'}
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '6px' }}>
              {isAdmin ? 'Can configure alert rules, restart/stop containers, and resolve incidents.' : 'Can view telemetry, charts, logs, and incidents without mutate permissions.'}
            </div>
          </div>

          <div style={{ padding: '16px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '6px' }}>Security Boundaries</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Socket Mount: <strong style={{ color: 'var(--status-healthy)' }}>Isolated Host Agent</strong></div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Secret Scrubbing: <strong style={{ color: 'var(--status-healthy)' }}>Active</strong></div>
          </div>
        </div>
      </div>

      {/* Administrative Audit Log */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <FileText size={18} style={{ color: 'var(--accent-cyan)' }} />
              <span>Administrative Action Audit Log</span>
            </div>
            <span className="card-subtitle">
              Immutable trail recording all container restarts, stops, rule changes, and incident resolutions
            </span>
          </div>
        </div>

        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Operator</th>
                <th>Action</th>
                <th>Target Type</th>
                <th>Target ID</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-dim)' }}>
                    No administrative actions recorded yet.
                  </td>
                </tr>
              ) : (
                auditLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="mono-cell" style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td style={{ fontWeight: 600 }}>{log.username}</td>
                    <td>
                      <span className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>
                        {log.action}
                      </span>
                    </td>
                    <td style={{ textTransform: 'uppercase', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {log.target_type || '-'}
                    </td>
                    <td className="mono-cell" style={{ color: 'var(--accent-cyan)', fontSize: '0.75rem' }}>
                      {log.target_id || '-'}
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {JSON.stringify(log.details)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* System Architecture & Health Details */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Database size={18} style={{ color: 'var(--accent-cyan)' }} />
            <span>System Health & Diagnostics</span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', fontSize: '0.85rem' }}>
          <div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Core Engine Version</div>
            <div style={{ fontWeight: 600, marginTop: '2px' }}>InfraPulse v{healthInfo?.version || '1.0.0'}</div>
          </div>

          <div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Database Backend</div>
            <div style={{ fontWeight: 600, color: 'var(--status-healthy)', marginTop: '2px' }}>
              {healthInfo?.database === 'connected' ? 'SQLite (Local) / PostgreSQL Ready' : 'Database Error'}
            </div>
          </div>

          <div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Monitored Containers</div>
            <div style={{ fontWeight: 600, marginTop: '2px' }}>{healthInfo?.containers_count ?? 0} active objects</div>
          </div>

          <div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Host Target Engines</div>
            <div style={{ fontWeight: 600, marginTop: '2px' }}>{healthInfo?.targets_count ?? 0} registered</div>
          </div>
        </div>
      </div>
    </div>
  );
}
