import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState({
    username: 'admin',
    role: 'admin',
    is_superuser: true,
  });
  const [loading, setLoading] = useState(true);

  const fetchCurrentUser = async () => {
    try {
      const data = await api.getMe();
      if (data.authenticated && data.user) {
        setUser(data.user);
      } else {
        // Default to admin for convenient local development
        setUser({ username: 'admin', role: 'admin', is_superuser: true });
      }
    } catch (_) {
      setUser({ username: 'admin', role: 'admin', is_superuser: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const login = async (username, password) => {
    const res = await api.login(username, password);
    setUser(res.user);
    return res.user;
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch (_) {}
    setUser({ username: 'operator', role: 'operator', is_superuser: false });
  };

  const switchRole = async (targetRole) => {
    try {
      if (targetRole === 'admin') {
        const u = await login('admin', 'admin123');
        setUser(u);
      } else {
        const u = await login('operator', 'operator123');
        setUser(u);
      }
    } catch (e) {
      console.warn('Switch role fallback to local simulation:', e);
      setUser({
        username: targetRole,
        role: targetRole,
        is_superuser: targetRole === 'admin',
      });
    }
  };

  const isAdmin = user?.role === 'admin' || user?.is_superuser;

  return (
    <AuthContext.Provider value={{ user, isAdmin, loading, login, logout, switchRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
