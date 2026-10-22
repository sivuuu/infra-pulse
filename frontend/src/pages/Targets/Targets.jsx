import React, { useState, useEffect } from 'react';
import { 
  Server, 
  CheckCircle2, 
  AlertOctagon, 
  Cpu, 
  HardDrive, 
  Activity, 
  ExternalLink,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';
import { api } from '../../api/client';

export default function Targets() {
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTargets = async () => {
    try {
      const data = await api.getTargets();
      setTargets(data.results || []);
    } catch (err) {
      console.error('Failed to load targets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTargets();
    const interval = setInterval(fetchTargets, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="content-body">
      {/* Target Nodes Grid */}
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>
        {targets.map((t) => {
          const isReachable = t.status === 'reachable';
          const meta = t.metadata || {};

          return (
            <div key={t.id} className="card" style={{ borderColor: isReachable ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div 
                    style={{ 
                      width: '36px', 
                      height: '36px', 
                      borderRadius: 'var(--radius-md)', 
                      background: isReachable ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      color: isReachable ? 'var(--status-healthy)' : 'var(--status-critical)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    <Server size={20} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>{t.name}</h3>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{t.hostname}</span>
                  </div>
                </div>

                <span className={`badge ${isReachable ? 'badge-healthy' : 'badge-critical'}`}>
                  {t.status.toUpperCase()}
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
                  <span>Runtime Engine:</span>
                  <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{t.runtime_type.toUpperCase()} ({meta.distribution || 'linux'})</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
                  <span>Containers Count:</span>
                  <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>
                    {t.running_containers_count} running / {t.containers_count} total
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
                  <span>Host Hardware:</span>
                  <span>{meta.cpus ? `${meta.cpus} vCPUs • ${(meta.memTotal ? meta.memTotal / (1024**3) : 0).toFixed(1)} GB RAM` : 'Local Host'}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
                  <span>Collector Endpoint:</span>
                  <span className="mono-cell" style={{ fontSize: '0.72rem' }}>{t.endpoint_url || 'local-agent'}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Last Seen / Heartbeat:</span>
                  <span className="mono-cell" style={{ fontSize: '0.72rem' }}>
                    {t.last_seen ? new Date(t.last_seen).toLocaleTimeString() : 'Never'}
                  </span>
                </div>
              </div>

              {t.error_message && (
                <div 
                  style={{ 
                    marginTop: '12px', 
                    padding: '8px 12px', 
                    borderRadius: 'var(--radius-sm)', 
                    background: 'var(--status-critical-bg)', 
                    color: 'var(--status-critical)',
                    fontSize: '0.75rem' 
                  }}
                >
                  Diagnostic: {t.error_message}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Prometheus Exposition Info Card */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <Activity size={18} style={{ color: 'var(--accent-cyan)' }} />
              <span>Prometheus Integration & Metrics Scraper</span>
            </div>
            <span className="card-subtitle">
              Native OpenMetrics / Prometheus exporter endpoint for enterprise federation
            </span>
          </div>

          <a 
            href="/metrics" 
            target="_blank" 
            rel="noopener noreferrer" 
            className="btn btn-secondary btn-sm"
          >
            <span>View /metrics Raw Stream</span>
            <ExternalLink size={14} />
          </a>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.85rem' }}>
          <p style={{ color: 'var(--text-muted)' }}>
            InfraPulse exposes standard Prometheus gauges and counters at <code>/metrics</code>, compliant with OpenMetrics exposition standards. Enterprise Prometheus servers can scrape this endpoint with least-privilege read access.
          </p>

          <div 
            style={{ 
              background: '#05080f', 
              padding: '14px 16px', 
              borderRadius: 'var(--radius-md)', 
              fontFamily: 'var(--font-mono)', 
              fontSize: '0.75rem', 
              color: '#38bdf8' 
            }}
          >
            <div># Sample prometheus.yml scrape config:</div>
            <div style={{ color: '#94a3b8' }}>scrape_configs:</div>
            <div style={{ color: '#94a3b8' }}>  - job_name: 'infrapulse-containers'</div>
            <div style={{ color: '#94a3b8' }}>    scrape_interval: 5s</div>
            <div style={{ color: '#94a3b8' }}>    static_configs:</div>
            <div style={{ color: '#94a3b8' }}>      - targets: ['localhost:8000']</div>
          </div>
        </div>
      </div>
    </div>
  );
}
