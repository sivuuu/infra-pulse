import React, { useState } from 'react';
import { RefreshCw, CheckCircle2, AlertOctagon } from 'lucide-react';
import { api } from '../../api/client';

export default function Topbar({ title, collectorStatus = 'healthy', freshnessSeconds = 0, onRefresh }) {
  const [syncing, setSyncing] = useState(false);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await api.triggerCollector();
      if (onRefresh) onRefresh();
    } catch (e) {
      console.error('Trigger collector failed:', e);
    } finally {
      setTimeout(() => setSyncing(false), 600);
    }
  };

  const isReachable = collectorStatus === 'healthy';

  return (
    <header className="topbar">
      <div className="topbar-left">
        <h1 className="page-title">{title}</h1>
      </div>

      <div className="topbar-right">
        <div 
          className="live-status-pill"
          style={{
            background: isReachable ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            borderColor: isReachable ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)',
            color: isReachable ? 'var(--status-healthy)' : 'var(--status-critical)'
          }}
        >
          <div className="pulsing-dot" style={{ background: isReachable ? 'var(--status-healthy)' : 'var(--status-critical)' }} />
          <span>{isReachable ? 'Podman Host Active' : 'Runtime Unreachable'}</span>
          {freshnessSeconds !== null && (
            <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem', marginLeft: '4px' }}>
              • {freshnessSeconds}s ago
            </span>
          )}
        </div>

        <button 
          onClick={handleSync}
          disabled={syncing}
          className="btn btn-secondary btn-sm"
          title="Trigger immediate metrics and container collection cycle"
        >
          <RefreshCw size={14} className={syncing ? 'spin-animation' : ''} />
          <span>{syncing ? 'Syncing...' : 'Sync Telemetry'}</span>
        </button>
      </div>
    </header>
  );
}
