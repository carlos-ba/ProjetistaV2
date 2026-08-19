import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || ''
});

// Injeta token em todo request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Se 401, tenta refresh; se falhar, desloga
api.interceptors.response.use(
  res => res,
  async error => {
    // Cobre tanto /api/auth/token/ (login) quanto /api/auth/token/refresh/ (refresh) —
    // um 401 nessas duas rotas significa credencial/refresh inválido, não sessão expirada.
    const ehLoginOuRefresh = error.config?.url?.includes('/auth/token/');
    if (error.response?.status === 401 && !error.config._retry && !ehLoginOuRefresh) {
      error.config._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const { data } = await api.post('/api/auth/token/refresh/', { refresh });
          localStorage.setItem('access_token', data.access);
          error.config.headers.Authorization = `Bearer ${data.access}`;
          return api(error.config);
        } catch {
          // cai no logout abaixo
        }
      }
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default api;
