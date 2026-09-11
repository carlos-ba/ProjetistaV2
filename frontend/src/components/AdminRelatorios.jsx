import { useEffect, useMemo, useState } from 'react';
import api from '../api';
import { PLANOS, STATUS, badgeStatus } from './AdminEmpresas';

/**
 * Relatórios de Administração — empresas/cadastros. Versão simples de
 * propósito (2026-09-11): "cadastros por dia" cruza com o status/plano
 * ATUAL de cada empresa, não com o status no dia do cadastro — não é um
 * funil de conversão ponto-a-ponto, é "quantos entraram e em que pé estão
 * hoje". Suficiente pra orientar marketing por ora.
 */

const formatarData = (iso) => {
  if (!iso) return null;
  return new Date(`${iso}T00:00:00`).toLocaleDateString('pt-BR');
};

export default function AdminRelatorios({ empresas }) {
  const [cadastros, setCadastros] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const [filtroStatus, setFiltroStatus] = useState('todos');
  const [filtroPlano, setFiltroPlano] = useState('todos');

  useEffect(() => {
    let cancelado = false;
    (async () => {
      setCarregando(true); setErro('');
      try {
        const { data } = await api.get('/api/v1/admin/relatorios/cadastros');
        if (!cancelado) setCadastros(data);
      } catch {
        if (!cancelado) setErro('Erro ao carregar o relatório de cadastros.');
      } finally {
        if (!cancelado) setCarregando(false);
      }
    })();
    return () => { cancelado = true; };
  }, []);

  const resumoStatus = useMemo(() => {
    const contagem = Object.fromEntries(STATUS.map(s => [s.id, 0]));
    for (const e of empresas) contagem[e.status_assinatura] = (contagem[e.status_assinatura] || 0) + 1;
    return contagem;
  }, [empresas]);

  const empresasFiltradas = useMemo(() => {
    return empresas
      .filter(e => filtroStatus === 'todos' || e.status_assinatura === filtroStatus)
      .filter(e => filtroPlano === 'todos' || e.plano === filtroPlano)
      // Sem vencimento (nunca expira) vai pro fim — não é urgente.
      .sort((a, b) => {
        if (!a.assinatura_fim && !b.assinatura_fim) return a.nome.localeCompare(b.nome);
        if (!a.assinatura_fim) return 1;
        if (!b.assinatura_fim) return -1;
        return a.assinatura_fim.localeCompare(b.assinatura_fim);
      });
  }, [empresas, filtroStatus, filtroPlano]);

  const cadastrosOrdenados = useMemo(
    () => [...cadastros].sort((a, b) => b.periodo.localeCompare(a.periodo)),
    [cadastros]
  );

  const campo = "px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs outline-none focus:ring-2 focus:ring-indigo-400";

  return (
    <div className="space-y-5">
      {erro && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 font-semibold">{erro}</div>}

      {/* Resumo por status */}
      <div className="grid grid-cols-4 gap-2">
        {STATUS.map(s => (
          <div key={s.id} className={`rounded-xl p-3 text-center ${s.cor}`}>
            <p className="text-2xl font-black">{resumoStatus[s.id] || 0}</p>
            <p className="text-[10px] font-bold uppercase">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Cadastros por dia */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <h4 className="text-xs font-black text-slate-700 uppercase mb-3">Cadastros por dia</h4>
        {carregando ? (
          <p className="text-center text-sm text-slate-400 py-4 animate-pulse">Carregando...</p>
        ) : cadastrosOrdenados.length === 0 ? (
          <p className="text-sm text-slate-400 italic">Nenhum cadastro registrado ainda.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-slate-400 uppercase text-[9px] border-b border-slate-100">
                  <th className="py-1.5 pr-3">Data</th>
                  <th className="py-1.5 pr-3">Total</th>
                  {PLANOS.map(p => <th key={p.id} className="py-1.5 pr-3">{p.label}</th>)}
                  {STATUS.map(s => <th key={s.id} className="py-1.5 pr-3">{s.label}</th>)}
                </tr>
              </thead>
              <tbody>
                {cadastrosOrdenados.map(c => (
                  <tr key={c.periodo} className="border-b border-slate-50">
                    <td className="py-1.5 pr-3 font-semibold text-slate-700">{formatarData(c.periodo)}</td>
                    <td className="py-1.5 pr-3 font-black text-slate-800">{c.total}</td>
                    {PLANOS.map(p => <td key={p.id} className="py-1.5 pr-3 text-slate-500">{c.por_plano[p.id] || 0}</td>)}
                    {STATUS.map(s => <td key={s.id} className="py-1.5 pr-3 text-slate-500">{c.por_status[s.id] || 0}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Empresas filtráveis, ordenadas por vencimento */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <h4 className="text-xs font-black text-slate-700 uppercase">Empresas — por vencimento</h4>
          <div className="flex gap-2">
            <select className={campo} value={filtroStatus} onChange={e => setFiltroStatus(e.target.value)}>
              <option value="todos">Todos os status</option>
              {STATUS.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
            </select>
            <select className={campo} value={filtroPlano} onChange={e => setFiltroPlano(e.target.value)}>
              <option value="todos">Todos os planos</option>
              {PLANOS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
            </select>
          </div>
        </div>
        {empresasFiltradas.length === 0 ? (
          <p className="text-sm text-slate-400 italic">Nenhuma empresa bate com esse filtro.</p>
        ) : (
          <div className="space-y-1.5">
            {empresasFiltradas.map(e => (
              <div key={e.id} className="flex items-center justify-between gap-3 rounded-lg border border-slate-100 px-3 py-2">
                <div className="min-w-0 flex items-center gap-2 flex-wrap">
                  <p className="text-sm font-semibold text-slate-800 truncate">{e.nome}</p>
                  <span className={`text-[9px] font-black px-2 py-0.5 rounded-full uppercase ${badgeStatus(e.status_assinatura)}`}>
                    {e.status_assinatura}
                  </span>
                  <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 uppercase">
                    {e.plano}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 flex-shrink-0">
                  {e.assinatura_fim ? `vence ${formatarData(e.assinatura_fim)}` : 'sem validade'}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
