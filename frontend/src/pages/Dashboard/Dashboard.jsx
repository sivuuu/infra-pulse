import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Box, 
  CheckCircle2, 
  AlertTriangle, 
  AlertOctagon, 
  Cpu, 
  HardDrive, 
  Clock, 
  ArrowRight,
  ShieldAlert,
  Server
} from 'lucide-react';
import { api } from '../../api/client';
import TimeSeriesChart from '../../components/MetricChart/TimeSeriesChart';
import StatusBadge from '../../components/StatusBadge/StatusBadge';

export default function Dashboard({ onSummaryLoaded }) {
  const [summary, setSummary] = useState(null);
  const [timeSeries, setTimeSeries] = useState({ points: [], window: '1h' });
  const [activeWindow, setActiveWindow] = useState('1h');
  const [recentIncidents, setRecentIncidents] = useState([]);
  const [containers, setContainers] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [sumData, tsData, incData, contData] = await Promise.all([
        api.getSummary(),
        api.getTimeSeries(activeWindow),
        api.getIncidents('firing'),
        api.getContainers({ limit: 8 }),
      ]);
      setSummary(sumData);
      setTimeSeries(tsData);
      setRecentIncidents(incData.results || []);
      setContainers(contData.results || []);
      if (onSummaryLoaded) onSummaryLoaded(sumData);
    } catch (err) {
      console.error('Failed to load dashboard telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [activeWindow]);

  const timestamps = (timeSeries.points || []).map((p) => p.timestamp);
  const cpuData = (timeSeries.points || []).map((p) => p.avg_cpu_percent);
  const memData = (timeSeries.points || []).map((p) => p.avg_memory_percent);

  return (
    <div className="content-body">
      {/* Stat Grid */}
      <div className="stat-grid">
        <div className="stat-card cyan">
          <div className="stat-header">
            <span className="stat-label">Total Containers</span>
            <div className="stat-icon" style={{ color: 'var(--accent-cyan)' }}>
              <Box size={18} />
            </div>
          </div>
          <div className="stat-value">{summary?.containers?.total ?? '-'}</div>
          <div className="stat-footer">
            <span>{summary?.containers?.running ?? 0} running active</span>
          </div>
        </div>

        <div className="stat-card green">
          <div className="stat-header">
            <span className="stat-label">Healthy Services</span>
            <div className="stat-icon" style={{ color: 'var(--status-healthy)' }}>
              <CheckCircle2 size={18} />
            </div>
          </div>
          <div className="stat-value" style={{ color: 'var(--status-healthy)' }}>
            {summary?.containers?.healthy ?? 0}
          </div>
          <div className="stat-footer">
            <span>Passed runtime health probes</span>
          </div>
        </div>

        <div className="stat-card amber">
          <div className="stat-header">
            <span className="stat-label">Unhealthy / Degraded</span>
            <div className="stat-icon" style={{ color: 'var(--status-warning)' }}>
              <AlertTriangle size={18} />
            </div>
          </div>
          <div className="stat-value" style={{ color: 'var(--status-warning)' }}>
            {summary?.containers?.unhealthy ?? 0}
          </div>
          <div className="stat-footer">
            <span>Failing application health check</span>
          </div>
        </div>

        <div className="stat-card red">
          <div className="stat-header">
            <span className="stat-label">Firing Incidents</span>
            <div className="stat-icon" style={{ color: 'var(--status-critical)' }}>
              <ShieldAlert size={18} />
            </div>
          </div>
          <div className="stat-value" style={{ color: 'var(--status-critical)' }}>
            {summary?.alerts?.firing ?? 0}
          </div>
          <div className="stat-footer">
            <span>{summary?.alerts?.critical ?? 0} critical severity</span>
          </div>
        </div>

        <div className="stat-card purple">
          <div className="stat-header">
            <span className="stat-label">Unreachable / Stale</span>
            <div className="stat-icon" style={{ color: 'var(--accent-purple)' }}>
              <Server size={18} />
            </div>
          </div>
          <div className="stat-value">{summary?.containers?.unreachable ?? 0}</div>
          <div className="stat-footer">
            <span>Targets with connection failure</span>
          </div>
        </div>
      </div>

      {/* Real-time Trend Charts */}
      <div className="charts-grid">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">
                <Cpu size={18} style={{ color: 'var(--accent-cyan)' }} />
                <span>CPU Consumption Trend</span>
              </div>
              <span className="card-subtitle">Aggregate system CPU percentage over time</span>
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

          <div className="chart-wrapper">
            <TimeSeriesChart
              labels={timestamps}
              yAxisLabel="%"
              datasets={[
                {
                  label: 'Avg CPU %',
                  data: cpuData,
                  borderColor: '#00f2fe',
                  backgroundColor: 'rgba(0, 242, 254, 0.1)',
                },
              ]}
            />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">
                <HardDrive size={18} style={{ color: '#818cf8' }} />
                <span>Memory Utilization Trend</span>
              </div>
              <span className="card-subtitle">Cluster memory allocation and assigned limits</span>
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

          <div className="chart-wrapper">
            <TimeSeriesChart
              labels={timestamps}
              yAxisLabel="%"
              datasets={[
                {
                  label: 'Avg Memory %',
                  data: memData,
                  borderColor: '#818cf8',
                  backgroundColor: 'rgba(129, 140, 248, 0.1)',
                },
              ]}
            />
          </div>
        </div>
      </div>

      {/* Lower Dashboard Section: Active Alerts Ticker & Container Quick Matrix */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '20px' }}>
        {/* Active Incidents Card */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">
                <AlertOctagon size={18} style={{ color: 'var(--status-critical)' }} />
                <span>Active Incidents</span>
              </div>
              <span className="card-subtitle">Firing alerts requiring DevOps investigation</span>
            </div>
            <Link to="/alerts" className="btn btn-secondary btn-sm">
              <span>View All</span>
              <ArrowRight size={14} />
            </Link>
          </div>

          {recentIncidents.length === 0 ? (
            <div style={{ padding: '36px 0', textAlign: 'center', color: 'var(--text-dim)' }}>
              <CheckCircle2 size={32} style={{ color: 'var(--status-healthy)', margin: '0 auto 12px' }} />
              <p style={{ fontWeight: 600, color: 'var(--text-main)' }}>All Systems Nominal</p>
              <p style={{ fontSize: '0.8rem' }}>No active firing incidents on monitored containers.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {recentIncidents.slice(0, 4).map((inc) => (
                <div
                  key={inc.id}
                  style={{
                    padding: '12px',
                    borderRadius: 'var(--radius-md)',
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{inc.rule_name}</span>
                    <span className={`badge ${inc.severity === 'critical' ? 'badge-critical' : 'badge-warning'}`}>
                      {inc.severity.toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Container: <strong>{inc.container_name}</strong>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} />
                    <span>First seen {new Date(inc.first_seen).toLocaleTimeString()} • Storm count: {inc.storm_count}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Monitored Containers Matrix */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">
                <Box size={18} style={{ color: 'var(--accent-cyan)' }} />
                <span>Container Fleet Status</span>
              </div>
              <span className="card-subtitle">Real-time status of local containers</span>
            </div>
            <Link to="/containers" className="btn btn-secondary btn-sm">
              <span>Inventory</span>
              <ArrowRight size={14} />
            </Link>
          </div>

          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Container</th>
                  <th>Status</th>
                  <th>Image</th>
                  <th>CPU</th>
                  <th>Memory</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {containers.slice(0, 6).map((c) => (
                  <tr key={c.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{c.name}</div>
                      <div className="mono-cell" style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>
                        {c.short_id}
                      </div>
                    </td>
                    <td>
                      <StatusBadge state={c.state} health={c.health_status} isStale={c.is_stale} />
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)', maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {c.image}
                    </td>
                    <td className="mono-cell">
                      {c.cpu_percent !== null && c.cpu_percent !== undefined ? (
                        <span style={{ color: c.cpu_percent > 80 ? 'var(--status-critical)' : 'var(--text-main)' }}>
                          {c.cpu_percent.toFixed(1)}%
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)' }}>--</span>
                      )}
                    </td>
                    <td className="mono-cell">
                      {c.memory_percent !== null && c.memory_percent !== undefined ? (
                        <span>{c.memory_percent.toFixed(1)}%</span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)' }}>--</span>
                      )}
                    </td>
                    <td>
                      <Link to={`/containers/${c.id}`} className="btn btn-secondary btn-sm">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
