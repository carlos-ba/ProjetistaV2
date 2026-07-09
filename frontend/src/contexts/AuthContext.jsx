import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const refresh = localStorage.getItem('refresh_token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        // Se o refresh token também já venceu, não há como renovar: descarta tudo
        const refreshPayload = refresh ? JSON.parse(atob(refresh.split('.')[1])) : null;
        const agora = Date.now() / 1000;
        if (!refreshPayload || refreshPayload.exp < agora) throw new Error('sessão expirada');
        setUser({ username: payload.username || payload.user_id });
      } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    const { data } = await api.post('/api/auth/token/', { username, password });
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    const payload = JSON.parse(atob(data.access.split('.')[1]));
    setUser({ username: payload.username || username });
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
