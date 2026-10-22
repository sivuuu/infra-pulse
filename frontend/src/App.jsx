import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Sidebar from './components/Layout/Sidebar';
import Topbar from './components/Layout/Topbar';
import Dashboard from './pages/Dashboard/Dashboard';
import Containers from './pages/Containers/Containers';
import ContainerDetail from './pages/ContainerDetail/ContainerDetail';
import Alerts from './pages/Alerts/Alerts';
import Logs from './pages/Logs/Logs';
import Targets from './pages/Targets/Targets';
import Settings from './pages/Settings/Settings';
import { AuthProvider } from './context/AuthContext';

function AppLayout() {
  const location = useLocation();
  const [summaryData, setSummaryData] = useState(null);

  const getPageTitle = (pathname) => {
    if (pathname === '/') return 'Executive Observability Dashboard';
    if (pathname.startsWith('/containers/') && pathname !== '/containers') return 'Container Deep Telemetry';
    if (pathname === '/containers') return 'Host & Container Inventory';
    if (pathname === '/alerts') return 'Alert Center & Incidents';
    if (pathname === '/logs') return 'Central Log Investigation Console';
    if (pathname === '/targets') return 'Monitoring Targets & Prometheus Diagnostics';
    if (pathname === '/settings') return 'Access Control, RBAC & Audit Log';
    return 'InfraPulse Observability';
  };

  const firingCount = summaryData?.alerts?.firing || 0;
  const collectorStatus = summaryData?.collector?.status || 'healthy';
  const freshnessSec = summaryData?.collector?.freshness_seconds ?? 0;

  return (
    <div className="app-container">
      <Sidebar firingAlertsCount={firingCount} />
      <div className="main-wrapper">
        <Topbar 
          title={getPageTitle(location.pathname)} 
          collectorStatus={collectorStatus}
          freshnessSeconds={freshnessSec}
          onRefresh={() => {
            // Trigger refresh
          }}
        />
        <main>
          <Routes>
            <Route path="/" element={<Dashboard onSummaryLoaded={setSummaryData} />} />
            <Route path="/containers" element={<Containers />} />
            <Route path="/containers/:id" element={<ContainerDetail />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/targets" element={<Targets />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </AuthProvider>
  );
}
