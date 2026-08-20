import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api';

// "há 2h", "há 5min" etc a partir de um ISO — só pra dar noção de quão parada
// está aquela sessão na hora de escolher qual encerrar.
const formatarUsoRelativo = (iso) => {
  if (!iso) return 'uso desconhecido';
  const diffMin = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (diffMin < 1) return 'agora mesmo';
  if (diffMin < 60) return `há ${diffMin} min`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `há ${diffH}h`;
  return `há ${Math.floor(diffH / 24)}d`;
};

export default function LoginPage() {
  const { login, loginEncerrandoSessao } = useAuth();
  const [aba, setAba] = useState('entrar'); // 'entrar' | 'cadastro'
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [erro, setErro] = useState('');
  const [sucesso, setSucesso] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessoesConflito, setSessoesConflito] = useState(null); // lista devolvida pelo 403 de limite
  const [encerrandoId, setEncerrandoId] = useState(null);

  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const handleLogin = async e => {
    e.preventDefault();
    setErro('');
    setSessoesConflito(null);
    setLoading(true);
    try {
      await login(form.username, form.password);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 403 && detail?.erro === 'limite_sessoes') {
        setErro(detail.mensagem || 'Limite de sessões atingido.');
        setSessoesConflito(detail.sessoes || []);
      } else {
        setErro(err.response?.status === 403 ? 'Limite de sessões atingido.' : 'Usuário ou senha inválidos.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleEncerrarSessao = async (sessaoId) => {
    setEncerrandoId(sessaoId);
    setErro('');
    try {
      await loginEncerrandoSessao(form.username, form.password, sessaoId);
    } catch {
      setErro('Não foi possível encerrar essa sessão. Tente novamente.');
    } finally {
      setEncerrandoId(null);
    }
  };

  const handleCadastro = async e => {
    e.preventDefault();
    setErro('');
    setSucesso('');
    setLoading(true);
    try {
      await api.post('/api/auth/register/', {
        username: form.username,
        email: form.email,
        password: form.password,
      });
      setSucesso('Conta criada! Faça login.');
      setAba('entrar');
      setForm(f => ({ ...f, password: '' }));
    } catch (err) {
      const data = err.response?.data;
      if (data) {
        const msgs = Object.values(data).flat().join(' ');
        setErro(msgs);
      } else {
        setErro('Erro ao criar conta.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#1a0d2e] via-[#2a1245] to-[#1a3a1a]">
      <div className="w-full max-w-md mx-4">
        {/* Logo / Título */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-3">
            <img src="/logo-icenexus.png" alt="IceNexus" className="h-10 w-auto object-contain" />
          </div>
          <p className="text-white/50 text-sm">Dimensionamento de câmaras frigoríficas</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Abas */}
          <div className="flex">
            <button
              onClick={() => { setAba('entrar'); setErro(''); setSucesso(''); setSessoesConflito(null); }}
              className={`flex-1 py-4 text-sm font-bold transition-colors ${aba === 'entrar' ? 'bg-[#7B2D8B] text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}
            >
              Entrar
            </button>
            <button
              onClick={() => { setAba('cadastro'); setErro(''); setSucesso(''); setSessoesConflito(null); }}
              className={`flex-1 py-4 text-sm font-bold transition-colors ${aba === 'cadastro' ? 'bg-[#7B2D8B] text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}
            >
              Criar Conta
            </button>
          </div>

          {/* Formulário */}
          <div className="p-8">
            {sucesso && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                {sucesso}
              </div>
            )}
            {erro && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {erro}
              </div>
            )}

            {sessoesConflito && sessoesConflito.length > 0 && (
              <div className="mb-4 space-y-2">
                {sessoesConflito.map(s => (
                  <div key={s.id} className="flex items-center justify-between gap-3 border border-slate-200 rounded-lg px-3 py-2">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-700 truncate">{s.dispositivo}</p>
                      <p className="text-[11px] text-slate-400">
                        {s.ip || 'IP desconhecido'} · {formatarUsoRelativo(s.ultimo_uso_em)}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleEncerrarSessao(s.id)}
                      disabled={encerrandoId === s.id}
                      className="flex-shrink-0 text-xs font-bold text-red-600 hover:underline disabled:opacity-50"
                    >
                      {encerrandoId === s.id ? 'Encerrando...' : 'Encerrar e continuar'}
                    </button>
                  </div>
                ))}
              </div>
            )}

            <form onSubmit={aba === 'entrar' ? handleLogin : handleCadastro} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Usuário</label>
                <input
                  type="text"
                  name="username"
                  value={form.username}
                  onChange={handleChange}
                  required
                  className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#7B2D8B] focus:border-transparent"
                  placeholder="seu_usuario"
                />
              </div>

              {aba === 'cadastro' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">E-mail</label>
                  <input
                    type="email"
                    name="email"
                    value={form.email}
                    onChange={handleChange}
                    className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#7B2D8B] focus:border-transparent"
                    placeholder="voce@email.com"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Senha</label>
                <input
                  type="password"
                  name="password"
                  value={form.password}
                  onChange={handleChange}
                  required
                  minLength={6}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#7B2D8B] focus:border-transparent"
                  placeholder="mínimo 6 caracteres"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#7B2D8B] hover:bg-purple-800 disabled:opacity-60 text-white font-bold py-3 rounded-lg text-sm transition-colors mt-2"
              >
                {loading ? 'Aguarde...' : aba === 'entrar' ? 'Entrar' : 'Criar Conta'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
