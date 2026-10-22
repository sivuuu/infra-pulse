import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  ShieldAlert, 
  CheckCircle2, 
  Clock, 
  Plus, 
  Trash2, 
  Check, 
  Sliders, 
  BellRing,
  Filter,
  X
} from 'lucide-react';
import { api } from '../../api/client';
import { useAuth } from '../../context/AuthContext';

export default function Alerts() {
  const { isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState('incidents'); // 'incidents' or 'rules'
  const [incidents, setIncidents] = useState([]);
  const [rules, setRules] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Modal states
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [showResolveModal, setShowResolveModal] = useState(null); // incident obj
  const [resolveNote, setResolveNote] = useState('');

  // New Rule Form
  const [newRule, setNewRule] = useState({
    name: '',
    description: '',
    metric: 'cpu_percent',
    condition: '>',
    threshold: 80,
    threshold_str: '',
    duration_seconds: 30,
    severity: 'warning',
    container_filter: '*',
  });

  const fetchData = async () => {
    try {
      const [incData, rulesData] = await Promise.all([
        api.getIncidents(statusFilter, severityFilter),
        api.getAlertRules(),
      ]);
      setIncidents(incData.results || []);
      setRules(rulesData.results || []);
    } catch (err) {
      console.error('Failed to load alert telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [statusFilter, severityFilter]);

  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    if (!showResolveModal) return;
    try {
      await api.resolveIncident(showResolveModal.id, resolveNote);
      setShowResolveModal(null);
      setResolveNote('');
      fetchData();
    } catch (err) {
      alert(`Failed to resolve incident: ${err.message}`);
    }
  };

  const handleCreateRuleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.createAlertRule(newRule);
      setShowRuleModal(false);
      setNewRule({
        name: '',
        description: '',
        metric: 'cpu_percent',
        condition: '>',
        threshold: 80,
        threshold_str: '',
        duration_seconds: 30,
        severity: 'warning',
        container_filter: '*',
      });
      fetchData();
    } catch (err) {
      alert(`Failed to create alert rule: ${err.message}`);
    }
  };

  const handleDeleteRule = async (id, name) => {
    if (!window.confirm(`Delete alert rule "${name}"?`)) return;
    try {
      await api.deleteAlertRule(id);
      fetchData();
    } catch (err) {
      alert(`Failed to delete rule: ${err.message}`);
    }
  };

  const handleToggleRule = async (rule) => {
    try {
      await api.updateAlertRule(rule.id, { enabled: !rule.enabled });
      fetchData();
    } catch (err) {
      alert(`Failed to update rule: ${err.message}`);
    }
  };

  return (
    <div className="content-body">
      {/* Tab Switcher & Action Button */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', gap: '8px', background: 'var(--bg-input)', padding: '4px', borderRadius: 'var(--radius-md)' }}>
          <button
            onClick={() => setActiveTab('incidents')}
            className={`btn btn-sm ${activeTab === 'incidents' ? 'btn-primary' : 'btn-secondary'}`}
          >
            <ShieldAlert size={14} />
            <span>Incident Timeline</span>
          </button>
          <button
            onClick={() => setActiveTab('rules')}
            className={`btn btn-sm ${activeTab === 'rules' ? 'btn-primary' : 'btn-secondary'}`}
          >
            <Sliders size={14} />
            <span>Alert Rules ({rules.length})</span>
          </button>
        </div>

        {activeTab === 'rules' && isAdmin && (
          <button onClick={() => setShowRuleModal(true)} className="btn btn-primary btn-sm">
            <Plus size={14} /> Create Alert Rule
          </button>
        )}
      </div>

      {/* Incidents View */}
      {activeTab === 'incidents' && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">
                <BellRing size={18} style={{ color: 'var(--status-critical)' }} />
                <span>Incident Stream & Deduplicated Events</span>
              </div>
              <span className="card-subtitle">
                State machine transitions with sliding evaluation window and storm suppression
              </span>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <select
                className="select-field"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="all">All Statuses</option>
                <option value="firing">Firing</option>
                <option value="pending">Pending Evaluation</option>
                <option value="resolved">Resolved</option>
              </select>

              <select
                className="select-field"
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
              >
                <option value="">All Severities</option>
                <option value="critical">Critical</option>
                <option value="warning">Warning</option>
                <option value="info">Info</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {incidents.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
                <CheckCircle2 size={36} style={{ color: 'var(--status-healthy)', margin: '0 auto 12px' }} />
                <p style={{ fontWeight: 600, color: 'var(--text-main)' }}>No Incidents In Selected Filter</p>
                <p style={{ fontSize: '0.8rem' }}>Container states and metrics are within configured thresholds.</p>
              </div>
            ) : (
              incidents.map((inc) => {
                const isFiring = inc.status === 'firing';
                const isPending = inc.status === 'pending';
                const isResolved = inc.status === 'resolved';

                return (
                  <div
                    key={inc.id}
                    style={{
                      padding: '16px 20px',
                      borderRadius: 'var(--radius-md)',
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: `1px solid ${isFiring ? 'rgba(239, 68, 68, 0.3)' : isPending ? 'rgba(245, 158, 11, 0.3)' : 'var(--border-subtle)'}`,
                      borderLeft: `4px solid ${isFiring ? 'var(--status-critical)' : isPending ? 'var(--status-warning)' : 'var(--status-healthy)'}`,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{inc.rule_name}</span>
                        <span className={`badge ${inc.severity === 'critical' ? 'badge-critical' : inc.severity === 'warning' ? 'badge-warning' : 'badge-cyan'}`}>
                          {inc.severity.toUpperCase()}
                        </span>
                        <span className={`badge ${isFiring ? 'badge-critical' : isPending ? 'badge-warning' : 'badge-healthy'}`}>
                          {inc.status.toUpperCase()}
                        </span>
                      </div>

                      {isAdmin && !isResolved && (
                        <button
                          onClick={() => setShowResolveModal(inc)}
                          className="btn btn-secondary btn-sm"
                        >
                          <Check size={12} /> Mark Resolved
                        </button>
                      )}
                    </div>

                    <div style={{ fontSize: '0.85rem', color: 'var(--text-main)' }}>
                      {inc.summary}
                    </div>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      <div>
                        Target Container: <strong>{inc.container_name}</strong>
                      </div>
                      <div>
                        First Seen: {new Date(inc.first_seen).toLocaleString()}
                      </div>
                      <div>
                        Last Seen: {new Date(inc.last_seen).toLocaleString()}
                      </div>
                      <div>
                        Storm Deduplications: <strong>{inc.storm_count} events</strong>
                      </div>
                      {inc.resolved_at && (
                        <div style={{ color: 'var(--status-healthy)' }}>
                          Resolved at: {new Date(inc.resolved_at).toLocaleString()} {inc.resolved_by_username ? `by ${inc.resolved_by_username}` : ''}
                        </div>
                      )}
                    </div>

                    {inc.resolution_note && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: 'rgba(255, 255, 255, 0.03)', padding: '6px 10px', borderRadius: '4px' }}>
                        Resolution Note: {inc.resolution_note}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Rules Manager View */}
      {activeTab === 'rules' && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">
                <Sliders size={18} style={{ color: 'var(--accent-cyan)' }} />
                <span>Configured Alert Rules</span>
              </div>
              <span className="card-subtitle">
                Evaluate metrics, health checks, restart counters, and reachability
              </span>
            </div>
          </div>

          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Rule Name</th>
                  <th>Metric & Condition</th>
                  <th>Window Duration</th>
                  <th>Severity</th>
                  <th>Scope Filter</th>
                  <th>Status</th>
                  {isAdmin && <th>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {rules.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{r.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{r.description}</div>
                    </td>
                    <td className="mono-cell">
                      {r.metric} {r.condition} {r.threshold_str || r.threshold}
                    </td>
                    <td className="mono-cell">
                      {r.duration_seconds}s
                    </td>
                    <td>
                      <span className={`badge ${r.severity === 'critical' ? 'badge-critical' : r.severity === 'warning' ? 'badge-warning' : 'badge-cyan'}`}>
                        {r.severity}
                      </span>
                    </td>
                    <td className="mono-cell" style={{ color: 'var(--accent-cyan)' }}>
                      {r.container_filter}
                    </td>
                    <td>
                      <button
                        disabled={!isAdmin}
                        onClick={() => handleToggleRule(r)}
                        className={`badge ${r.enabled ? 'badge-healthy' : 'badge-stopped'}`}
                        style={{ cursor: isAdmin ? 'pointer' : 'default', border: 'none' }}
                      >
                        {r.enabled ? 'Enabled' : 'Disabled'}
                      </button>
                    </td>
                    {isAdmin && (
                      <td>
                        <button
                          onClick={() => handleDeleteRule(r.id, r.name)}
                          className="btn btn-danger btn-sm"
                          title="Delete rule"
                        >
                          <Trash2 size={12} />
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Resolve Incident Modal */}
      {showResolveModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Resolve Incident #{showResolveModal.id}</h3>
              <button onClick={() => setShowResolveModal(null)} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleResolveSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                  Incident Rule
                </label>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                  {showResolveModal.rule_name} on {showResolveModal.container_name}
                </div>
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                  Resolution Note / Action Taken
                </label>
                <textarea
                  className="input-field"
                  rows="3"
                  style={{ width: '100%', resize: 'none' }}
                  placeholder="e.g. Memory leak investigated and service reconfigured."
                  value={resolveNote}
                  onChange={(e) => setResolveNote(e.target.value)}
                  required
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" onClick={() => setShowResolveModal(null)} className="btn btn-secondary btn-sm">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Confirm Resolution
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Rule Modal */}
      {showRuleModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Create New Alert Rule</h3>
              <button onClick={() => setShowRuleModal(false)} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleCreateRuleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Rule Name</label>
                <input
                  type="text"
                  className="input-field"
                  required
                  value={newRule.name}
                  onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                  placeholder="e.g. CPU Spike Above 90%"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Metric</label>
                  <select
                    className="select-field"
                    style={{ width: '100%' }}
                    value={newRule.metric}
                    onChange={(e) => setNewRule({ ...newRule, metric: e.target.value })}
                  >
                    <option value="cpu_percent">CPU %</option>
                    <option value="memory_percent">Memory %</option>
                    <option value="health_status">Health Status</option>
                    <option value="state">Container State</option>
                    <option value="restart_count">Restart Count</option>
                    <option value="reachability">Host Reachability</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Condition</label>
                  <select
                    className="select-field"
                    style={{ width: '100%' }}
                    value={newRule.condition}
                    onChange={(e) => setNewRule({ ...newRule, condition: e.target.value })}
                  >
                    <option value=">">&gt; (Greater than)</option>
                    <option value=">=">&gt;= (Greater or equal)</option>
                    <option value="<">&lt; (Less than)</option>
                    <option value="<=">&lt;= (Less or equal)</option>
                    <option value="==">== (Equals)</option>
                    <option value="!=">!= (Not equals)</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Numeric Threshold</label>
                  <input
                    type="number"
                    step="0.1"
                    className="input-field"
                    value={newRule.threshold}
                    onChange={(e) => setNewRule({ ...newRule, threshold: parseFloat(e.target.value) || 0 })}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Duration Before Firing (sec)</label>
                  <input
                    type="number"
                    className="input-field"
                    value={newRule.duration_seconds}
                    onChange={(e) => setNewRule({ ...newRule, duration_seconds: parseInt(e.target.value, 10) || 0 })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Severity</label>
                  <select
                    className="select-field"
                    style={{ width: '100%' }}
                    value={newRule.severity}
                    onChange={(e) => setNewRule({ ...newRule, severity: e.target.value })}
                  >
                    <option value="critical">Critical</option>
                    <option value="warning">Warning</option>
                    <option value="info">Info</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Container Scope Filter</label>
                  <input
                    type="text"
                    className="input-field"
                    value={newRule.container_filter}
                    onChange={(e) => setNewRule({ ...newRule, container_filter: e.target.value })}
                    placeholder="* or regex pattern"
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
                <button type="button" onClick={() => setShowRuleModal(false)} className="btn btn-secondary btn-sm">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Save Alert Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
