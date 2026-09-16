import { useEffect, useMemo, useState } from 'react';
import api from '../api';

/**
 * Atividade de Usuários — grão de usuário, não de empresa (decisão do
 * usuário, 2026-09-16): hoje o cadastro que importa monitorar é o
 * individual (self-serve, 1 empresa por usuário) — empresa com equipe de
 * verdade ainda é exceção. `membros_empresa` já deixa esse relatório
 * pronto pra quando isso mudar, sem precisar redesenhar nada: com 1 membro
 * só, mostra "conta individual"; com mais, mostra o nome real da empresa.
 */

const DIAS_ATIVO = 7;

const formatarData = (iso) => {
  if (!iso) return null;
  return new Date(iso).toLocaleDateString('pt-BR');
};

const diasDesde = (iso) => {
  if (!iso) return null;
  const ms = Date.now() - new Date(iso).getTime();
  return Math.floor(ms / (1000 * 60 * 60 * 24));
};

export default function AdminAtividade() {
  const [linhas, setLinhas] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');

  useEffect(() => {
    let cancelado = false;
    (async () => {
      setCarregando(true); setErro('');
      try {
        const { data } = await api.get('/api/v1/admin/relatorios/atividade-usuarios');
        if (!cancelado) setLinhas(data);
      } catch {
        if (!cancelado) setErro('Erro ao carregar a atividade de usuários.');
      } finally {
        if (!cancelado) setCarregando(false);
      }
    })();
    return () => { cancelado = true; };
  }, []);

  // Quem sumiu há mais tempo aparece primeiro — mesmo raciocínio de "quem
  // vence primeiro aparece primeiro" já usado na lista de empresas por
  // vencimento. Nunca acessou vai pro topo (pior sinal possível).
  const ordenadas = useMemo(() => {
    return [...linhas].sort((a, b) => {
      if (!a.ultimo_acesso && !b.ultimo_acesso) return a.username.localeCompare(b.username);
      if (!a.ultimo_acesso) return -1;
      if (!b.ultimo_acesso) return 1;
      return a.ultimo_acesso.localeCompare(b.ultimo_acesso);
    });
  }, [linhas]);

  if (carregando) {
    return <p className="text-center text-sm text-slate-400 py-8 animate-pulse">Carregando...</p>;
  }

  return (
    <div className="space-y-4">
      {erro && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 font-semibold">{erro}</div>}

      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <h4 className="text-xs font-black text-slate-700 uppercase mb-3">Atividade por usuário</h4>
        {ordenadas.length === 0 ? (
          <p className="text-sm text-slate-400 italic">Nenhum usuário cadastrado ainda.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-slate-400 uppercase text-[9px] border-b border-slate-100">
                  <th className="py-1.5 pr-3">Usuário</th>
                  <th className="py-1.5 pr-3">Empresa</th>
                  <th className="py-1.5 pr-3">Cadastrado em</th>
                  <th className="py-1.5 pr-3">Acessos</th>
                  <th className="py-1.5 pr-3">Dias Distintos</th>
                  <th className="py-1.5 pr-3">Último Acesso</th>
                  <th className="py-1.5 pr-3">Projetos</th>
                </tr>
              </thead>
              <tbody>
                {ordenadas.map(l => {
                  const dias = diasDesde(l.ultimo_acesso);
                  const ativo = dias !== null && dias <= DIAS_ATIVO;
                  return (
                    <tr key={l.usuario_id} className="border-b border-slate-50">
                      <td className="py-1.5 pr-3 font-semibold text-slate-700">{l.username}</td>
                      <td className="py-1.5 pr-3 text-slate-500">
                        {l.membros_empresa <= 1 ? (
                          <span className="text-slate-400 italic">conta individual</span>
                        ) : (
                          <>{l.empresa_nome} <span className="text-slate-400">({l.membros_empresa} membros)</span></>
                        )}
                      </td>
                      <td className="py-1.5 pr-3 text-slate-500">{formatarData(l.usuario_criado_em)}</td>
                      <td className="py-1.5 pr-3 font-black text-slate-800">{l.total_acessos}</td>
                      <td className="py-1.5 pr-3 text-slate-500">{l.dias_distintos_acesso}</td>
                      <td className="py-1.5 pr-3">
                        {l.ultimo_acesso ? (
                          <span className={`text-[9px] font-black px-2 py-0.5 rounded-full uppercase ${ativo ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                            há {dias} {dias === 1 ? 'dia' : 'dias'}
                          </span>
                        ) : (
                          <span className="text-[9px] font-black px-2 py-0.5 rounded-full uppercase bg-red-50 text-red-500">
                            nunca acessou
                          </span>
                        )}
                      </td>
                      <td className="py-1.5 pr-3 text-slate-500">{l.total_projetos}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
