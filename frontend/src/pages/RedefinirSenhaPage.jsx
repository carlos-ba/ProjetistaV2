import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import api from '../api';

export default function RedefinirSenhaPage() {
  const [token] = useState(() => new URLSearchParams(window.location.search).get('token'));
  const [senha, setSenha] = useState('');
  const [confirmarSenha, setConfirmarSenha] = useState('');
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [status, setStatus] = useState('formulario'); // 'formulario' | 'sucesso'
  const [erro, setErro] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async e => {
    e.preventDefault();
    setErro('');
    if (senha.length < 6) {
      setErro('A senha precisa ter ao menos 6 caracteres.');
      return;
    }
    if (senha !== confirmarSenha) {
      setErro('As senhas não coincidem.');
      return;
    }
    setLoading(true);
    try {
      await api.post('/api/auth/reset-password/', { token, nova_senha: senha });
      setStatus('sucesso');
    } catch (err) {
      setErro(err.response?.data?.detail || 'Link inválido ou expirado.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#1a0d2e] via-[#2a1245] to-[#1a3a1a]">
      <div className="w-full max-w-md mx-4">
        <div className="text-center mb-8">
          <img src="/logo-icenexus.png" alt="IceNexus" className="h-10 w-auto object-contain mx-auto" />
        </div>
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {!token ? (
            <div className="text-center">
              <div className="text-4xl mb-3">⚠️</div>
              <p className="text-red-700 text-sm mb-6">Link inválido — token não encontrado.</p>
              <a
                href="/"
                className="inline-block px-6 py-2.5 bg-[#7B2D8B] hover:bg-purple-800 text-white rounded-lg font-bold text-sm transition-colors"
              >
                Voltar para o login
              </a>
            </div>
          ) : status === 'sucesso' ? (
            <div className="text-center">
              <div className="text-4xl mb-3">✅</div>
              <p className="text-green-700 text-sm mb-6">Senha redefinida com sucesso. Você já pode fazer login.</p>
              <a
                href="/"
                className="inline-block px-6 py-2.5 bg-[#7B2D8B] hover:bg-purple-800 text-white rounded-lg font-bold text-sm transition-colors"
              >
                Ir para o login
              </a>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <h2 className="text-lg font-black text-slate-900">Criar nova senha</h2>
              {erro && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {erro}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Nova senha</label>
                <div className="relative">
                  <input
                    type={mostrarSenha ? 'text' : 'password'}
                    value={senha}
                    onChange={e => setSenha(e.target.value)}
                    required
                    minLength={6}
                    className="w-full border border-slate-300 rounded-lg pl-3 pr-10 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#7B2D8B] focus:border-transparent"
                    placeholder="mínimo 6 caracteres"
                  />
                  <button
                    type="button"
                    onClick={() => setMostrarSenha(v => !v)}
                    tabIndex={-1}
                    className="absolute right-0 top-0 h-full px-3 flex items-center text-slate-400 hover:text-slate-600"
                    title={mostrarSenha ? 'Ocultar senha' : 'Mostrar senha'}
                  >
                    {mostrarSenha ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Confirmar nova senha</label>
                <input
                  type={mostrarSenha ? 'text' : 'password'}
                  value={confirmarSenha}
                  onChange={e => setConfirmarSenha(e.target.value)}
                  required
                  minLength={6}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#7B2D8B] focus:border-transparent"
                  placeholder="repita a senha"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#7B2D8B] hover:bg-purple-800 disabled:opacity-60 text-white font-bold py-3 rounded-lg text-sm transition-colors"
              >
                {loading ? 'Aguarde...' : 'Redefinir senha'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
