import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Busca o usuário completo (inclui modo_engenharia); fallback para o username do JWT
  const carregarUsuario = async (token, fallbackUsername) => {
    try {
      const { data } = await api.get('/api/auth/me/');
      setUser(data);
    } catch {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser({ username: payload.username || fallbackUsername || payload.user_id });
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const refresh = localStorage.getItem('refresh_token');
    if (token) {
      try {
        // Se o refresh token também já venceu, não há como renovar: descarta tudo
        const refreshPayload = refresh ? JSON.parse(atob(refresh.split('.')[1])) : null;
        const agora = Date.now() / 1000;
        if (!refreshPayload || refreshPayload.exp < agora) throw new Error('sessão expirada');
        carregarUsuario(token).finally(() => setLoading(false));
        return;
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
    await carregarUsuario(data.access, username);
  };

  // Atualiza o modo do app (engenharia × completo) e reflete no contexto
  const atualizarModoEngenharia = async (valor) => {
    const { data } = await api.patch('/api/auth/me/preferencias/', { modo_engenharia: valor });
    setUser(data);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, atualizarModoEngenharia }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
