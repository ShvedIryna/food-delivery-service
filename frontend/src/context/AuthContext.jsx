import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api, getToken, setToken } from '../api.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(getToken()));

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      return null;
    }
    try {
      const me = await api('/me');
      setUser(me);
      return me;
    } catch {
      setToken(null);
      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  const applyToken = (data) => {
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const login = async (email, password) =>
    applyToken(await api('/auth/login', { method: 'POST', body: { email, password } }));

  const register = async (form) =>
    applyToken(await api('/auth/register', { method: 'POST', body: form }));

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refresh, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
