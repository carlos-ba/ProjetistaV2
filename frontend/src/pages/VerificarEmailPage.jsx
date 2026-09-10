import { useEffect, useRef, useState } from 'react';
import api from '../api';

export default function VerificarEmailPage() {
  const [status, setStatus] = useState('verificando'); // 'verificando' | 'sucesso' | 'erro'
  const [mensagem, setMensagem] = useState('');
  // Token é de uso único (o backend invalida após verificar) — sem essa trava,
  // o StrictMode do React (dev) chama o efeito 2x e a 2ª tentativa reusa um
  // token já consumido, sobrescrevendo "sucesso" com "erro" na tela.
  const jaTentouRef = useRef(false);

  useEffect(() => {
    if (jaTentouRef.current) return;
    jaTentouRef.current = true;

    const token = new URLSearchParams(window.location.search).get('token');
    if (!token) {
      setStatus('erro');
      setMensagem('Link inválido — token não encontrado.');
      return;
    }
    api.get('/api/auth/verify-email/', { params: { token } })
      .then(res => {
        setStatus('sucesso');
        setMensagem(res.data?.detail || 'Email verificado com sucesso.');
      })
      .catch(err => {
        setStatus('erro');
        setMensagem(err.response?.data?.detail || 'Link inválido ou expirado.');
      });
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#1a0d2e] via-[#2a1245] to-[#1a3a1a]">
      <div className="w-full max-w-md mx-4">
        <div className="text-center mb-8">
          <img src="/logo-icenexus.png" alt="IceNexus" className="h-10 w-auto object-contain mx-auto" />
        </div>
        <div className="bg-white rounded-2xl shadow-2xl p-8 text-center">
          {status === 'verificando' && (
            <>
              <div className="w-10 h-10 border-4 border-slate-200 border-t-[#7B2D8B] rounded-full animate-spin mx-auto mb-4" />
              <p className="text-slate-600 text-sm">Verificando seu email...</p>
            </>
          )}
          {status === 'sucesso' && (
            <>
              <div className="text-4xl mb-3">✅</div>
              <p className="text-green-700 text-sm mb-6">{mensagem}</p>
              <a
                href="/"
                className="inline-block px-6 py-2.5 bg-[#7B2D8B] hover:bg-purple-800 text-white rounded-lg font-bold text-sm transition-colors"
              >
                Ir para o login
              </a>
            </>
          )}
          {status === 'erro' && (
            <>
              <div className="text-4xl mb-3">⚠️</div>
              <p className="text-red-700 text-sm mb-6">{mensagem}</p>
              <a
                href="/"
                className="inline-block px-6 py-2.5 bg-[#7B2D8B] hover:bg-purple-800 text-white rounded-lg font-bold text-sm transition-colors"
              >
                Voltar para o login
              </a>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
