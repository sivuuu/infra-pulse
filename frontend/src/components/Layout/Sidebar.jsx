import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Activity, 
  Box, 
  AlertTriangle, 
  Terminal, 
  Server, 
  Settings, 
  ShieldCheck, 
  UserCheck 
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function Sidebar({ firingAlertsCount = 0 }) {
  const { user, isAdmin, switchRole } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon-wrapper">
          <Activity size={22} strokeWidth={2.5} />
        </div>
        <div className="brand-name">InfraPulse</div>
        <span className="brand-tag">CORE</span>
      </div>

      <nav className="nav-menu">
        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Activity size={18} />
          <span className="nav-text">Overview</span>
        </NavLink>

        <NavLink to="/containers" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Box size={18} />
          <span className="nav-text">Containers</span>
        </NavLink>

        <NavLink to="/alerts" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <AlertTriangle size={18} />
          <span className="nav-text">Alert Center</span>
          {firingAlertsCount > 0 && (
            <span className="nav-badge danger">{firingAlertsCount}</span>
          )}
        </NavLink>

        <NavLink to="/logs" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Terminal size={18} />
          <span className="nav-text">Logs Explorer</span>
        </NavLink>

        <NavLink to="/targets" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Server size={18} />
          <span className="nav-text">Host Targets</span>
        </NavLink>

        <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Settings size={18} />
          <span className="nav-text">Settings & Audit</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="user-badge-card">
          <div className="user-avatar">
            {user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="user-info">
            <span className="user-name">{user?.username}</span>
            <span className="user-role">
              {isAdmin ? 'Administrator' : 'Read-Only Operator'}
            </span>
          </div>
        </div>

        <div style={{ marginTop: '10px', display: 'flex', gap: '6px' }}>
          <button
            onClick={() => switchRole(isAdmin ? 'operator' : 'admin')}
            className="btn btn-secondary btn-sm"
            style={{ width: '100%', fontSize: '0.7rem' }}
            title="Toggle between Admin and Operator RBAC roles"
          >
            {isAdmin ? 'Switch to Operator' : 'Switch to Admin'}
          </button>
        </div>
      </div>
    </aside>
  );
}
