import React from 'react';

export default function StatusBadge({ state, health, isStale }) {
  if (isStale) {
    return <span className="badge badge-unreachable">Stale Target</span>;
  }

  // Health priority
  if (health === 'unhealthy') {
    return <span className="badge badge-critical">Unhealthy</span>;
  }
  if (health === 'unreachable') {
    return <span className="badge badge-unreachable">Unreachable</span>;
  }

  // State
  const s = (state || 'unknown').toLowerCase();
  if (s === 'running') {
    return <span className="badge badge-healthy">Running</span>;
  }
  if (s === 'exited') {
    return <span className="badge badge-warning">Exited</span>;
  }
  if (s === 'stopped') {
    return <span className="badge badge-stopped">Stopped</span>;
  }
  if (s === 'paused') {
    return <span className="badge badge-cyan">Paused</span>;
  }
  if (s === 'dead') {
    return <span className="badge badge-critical">Dead</span>;
  }

  return <span className="badge badge-stopped">{state || 'Unknown'}</span>;
}
