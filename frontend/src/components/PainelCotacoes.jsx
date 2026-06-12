import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import api from '../api';

/**
 * Painel de Cotações (Fase 2).
 *
 * - Lista as cotações do usuário com status
 * - Importa a planilha devolvida pelo fornecedor:
 *     upload → análise (nada gravado) → tela de conferência → confirmar
 */
const STATUS_BADGE = {
  rascunho:   'bg-slate-100 text-slate-600',
  enviada:    'bg-amber-100 text-amber-700',
  recebida:   'bg-blue-100 text-blue-700',
  processada: 'bg-emerald-100 text-emerald-700',
  cancelada:  'bg-red-100 text-red-500',
};

const ITEM_STATUS = {
  ok:             { cor: 'bg-emerald-50 border-emerald-200', label: '✅ Preço lido',        txt: 'text-emerald-700' },
  sem_preco:      { cor: 'bg-amber-50 border-amber-200',     label: '⚠️ Sem preço',         txt: 'text-amber-700' },
  preco_invalido: { cor: 'bg-red-50 border-red-200',         label: '❌ Preço ilegível',    txt: 'text-red-600' },
  nao_encontrado: { cor: 'bg-red-50 border-red-200',         label: '❌ Não encontrado',    txt: 'text-red-600' },
  linha_extra:    { cor: 'bg-blue-50 border-blue-200',       label: 'ℹ️ Linha extra',       txt: 'text-blue-600' },
};

const PainelCotacoes = ({ aberto, aoFechar }) => {
  const [cotacoes, setCotacoes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState('');

  // Fluxo de importação
  const [analise, setAnalise] = useState(null);       // resultado do /analisar
  const [edicao, setEdicao] = useState({});           // { item_id: { preco, marca, prazo, obs } }
  const [importando, setImportando] = useState(false);
  const [sucessoImport, setSucessoImport] = useState(null);
  const fileRef = useRef(null);

  useEffect(() => {
    if (aberto) {
      setErro(''); setAnalise(null); setSucessoImport(null);
      carregar();
    }
  }, [aberto]);

  const carregar = async () => {
    setLoading(true);
    try {
      const r = await api.get('/api/v1/cotacoes');
      setCotacoes(r.data);
    } catch {
      setErro('Erro ao carregar cotações.');
    } finally {
      setLoading(false);
    }
  };

  const baixarExcel = async (cot) => {
    try {
      const resp = await api.get(`/api/v1/cotacoes/${cot.id}/excel`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${cot.codigo}.xlsx`);
      document.body.appendChild(link); link.click(); link.remove();
      carregar();
    } catch { setErro('Erro ao baixar a planilha.'); }
  };

  // ── Importação ─────────────────────────────────────────────────────────
  const analisarArquivo = async (file) => {
    if (!file) return;
    setImportando(true); setErro(''); setSucessoImport(null);
    try {
      const form = new FormData();
      form.append('arquivo', file);
      const r = await api.post('/api/v1/cotacoes/importar/analisar', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setAnalise(r.data);
      // Pré-carrega os campos editáveis com o que foi lido
      const ed = {};
      r.data.itens.forEach(it => {
        if (it.item_id) {
          ed[it.item_id] = {
            preco: it.preco_unitario ?? '',
            marca: it.marca_modelo ?? '',
            prazo: it.prazo_dias ?? '',
            obs: it.obs ?? '',
          };
        }
      });
      setEdicao(ed);
    } catch (e) {
      setErro(e.response?.data?.detail || 'Erro ao analisar a planilha.');
    } finally {
      setImportando(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const updateEdicao = (id, campo, valor) =>
    setEdicao(p => ({ ...p, [id]: { ...p[id], [campo]: valor } }));

  const confirmarImportacao = async () => {
    setImportando(true); setErro('');
    try {
      const itens = Object.entries(edicao).map(([id, e]) => ({
        item_id: parseInt(id),
        preco_unitario: e.preco !== '' ? parseFloat(e.preco) : null,
        marca_modelo_cotado: e.marca || null,
        prazo_entrega_dias: e.prazo !== '' ? parseInt(e.prazo) : null,
        obs_fornecedor: e.obs || null,
      }));
      await api.post(`/api/v1/cotacoes/${analise.cotacao_id}/importar/confirmar`, { itens });
      setSucessoImport(analise.codigo);
      setAnalise(null);
      carregar();
    } catch (e) {
      setErro(e.response?.data?.detail || 'Erro ao confirmar a importação.');
    } finally {
      setImportando(false);
    }
  };

  if (!aberto) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">

        {/* Header */}
        <div className="bg-slate-900 px-6 py-4 flex items-center justify-between flex-shrink-0">
          <h3 className="text-white font-bold flex items-center gap-2">📊 Minhas Cotações</h3>
          <button onClick={aoFechar} className="text-white/60 hover:text-white text-xl leading-none">✕</button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-5">

          {erro && <p className="text-sm text-red-600 font-bold bg-red-50 rounded-lg px-3 py-2 border border-red-200">{erro}</p>}
          {sucessoImport && (
            <p className="text-sm text-emerald-700 font-bold bg-emerald-50 rounded-lg px-3 py-2 border border-emerald-200">
              ✅ Cotação {sucessoImport} importada com sucesso! Preços gravados no histórico.
            </p>
          )}

          {/* ── Tela de conferência ── */}
          {analise ? (
            <div className="space-y-4">
              <div className="bg-indigo-50 rounded-xl px-4 py-3 border border-indigo-200">
                <p className="font-bold text-indigo-900 text-sm">
                  Conferência — {analise.codigo} · {analise.fornecedor}
                </p>
                <p className="text-xs text-indigo-700 mt-1">
                  {analise.resumo.ok} com preço · {analise.resumo.sem_preco} sem preço ·{' '}
                  {analise.resumo.preco_invalido} ilegíveis · {analise.resumo.linha_extra} linhas extras
                </p>
                {analise.ja_processada && (
                  <p className="text-xs text-amber-700 font-bold mt-1">
                    ⚠️ Esta cotação já foi processada antes — confirmar vai sobrescrever os preços.
                  </p>
                )}
              </div>

              <div className="space-y-2">
                {analise.itens.map((it, idx) => {
                  const st = ITEM_STATUS[it.status] || ITEM_STATUS.ok;
                  const ed = it.item_id ? edicao[it.item_id] : null;
                  return (
                    <div key={idx} className={`rounded-xl border p-3 ${st.cor}`}>
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <p className="text-sm font-bold text-slate-800 leading-tight">
                          {it.descricao}
                          <span className="font-normal text-slate-500 ml-2 text-xs">{it.qtde} {it.unidade}</span>
                        </p>
                        <span className={`text-[10px] font-bold whitespace-nowrap ${st.txt}`}>{st.label}</span>
                      </div>

                      {it.status === 'preco_invalido' && (
                        <p className="text-[10px] text-red-500 mb-2">
                          Texto lido: "{it.preco_bruto}" — corrija o valor abaixo
                        </p>
                      )}
                      {it.status === 'linha_extra' && (
                        <p className="text-[10px] text-blue-500">
                          Item adicionado pelo fornecedor — não será importado (Fase 1).
                          {it.preco_unitario ? ` Preço informado: R$ ${it.preco_unitario}` : ''}
                        </p>
                      )}

                      {ed && (
                        <div className="grid grid-cols-12 gap-2">
                          <div className="col-span-3 relative">
                            <span className="absolute left-2 top-1.5 text-slate-400 text-xs">R$</span>
                            <input type="number" step="0.01" min="0" value={ed.preco}
                              onChange={e => updateEdicao(it.item_id, 'preco', e.target.value)}
                              className="w-full pl-7 pr-2 py-1.5 rounded-lg border border-slate-300 text-xs outline-none bg-white" />
                          </div>
                          <input value={ed.marca} placeholder="Marca/modelo ofertado"
                            onChange={e => updateEdicao(it.item_id, 'marca', e.target.value)}
                            className="col-span-4 px-2 py-1.5 rounded-lg border border-slate-300 text-xs outline-none bg-white" />
                          <input type="number" min="0" value={ed.prazo} placeholder="Prazo"
                            onChange={e => updateEdicao(it.item_id, 'prazo', e.target.value)}
                            className="col-span-2 px-2 py-1.5 rounded-lg border border-slate-300 text-xs text-center outline-none bg-white" />
                          <input value={ed.obs} placeholder="Obs"
                            onChange={e => updateEdicao(it.item_id, 'obs', e.target.value)}
                            className="col-span-3 px-2 py-1.5 rounded-lg border border-slate-300 text-xs outline-none bg-white" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button onClick={() => setAnalise(null)}
                  className="px-4 py-2 text-slate-500 hover:text-slate-700 text-sm font-bold">
                  Cancelar
                </button>
                <button onClick={confirmarImportacao} disabled={importando}
                  className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-sm shadow transition-all disabled:opacity-40">
                  {importando ? 'Gravando...' : '✅ CONFIRMAR E GRAVAR PREÇOS'}
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* ── Botão de importar ── */}
              <div className="bg-amber-50 rounded-xl border-2 border-dashed border-amber-300 p-5 text-center">
                <p className="text-sm font-bold text-amber-800 mb-1">📥 Recebeu a planilha preenchida do fornecedor?</p>
                <p className="text-xs text-amber-600 mb-3">
                  O sistema identifica a cotação pelo código e mostra os preços para conferência antes de gravar.
                </p>
                <input ref={fileRef} type="file" accept=".xlsx,.xlsm" className="hidden"
                  onChange={e => analisarArquivo(e.target.files[0])} />
                <button onClick={() => fileRef.current?.click()} disabled={importando}
                  className="px-6 py-2.5 bg-amber-500 hover:bg-amber-600 text-white rounded-xl font-bold text-sm shadow transition-all disabled:opacity-40">
                  {importando ? 'Analisando...' : 'SELECIONAR ARQUIVO EXCEL'}
                </button>
              </div>

              {/* ── Lista de cotações ── */}
              <div>
                <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3">Cotações geradas</h4>
                {loading ? (
                  <p className="text-sm text-slate-400 animate-pulse">Carregando...</p>
                ) : cotacoes.length === 0 ? (
                  <p className="text-sm text-slate-400 italic">
                    Nenhuma cotação ainda. Gere uma no card de Orçamento do seu projeto.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {cotacoes.map(c => (
                      <div key={c.id} className="flex items-center justify-between gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <div className="min-w-0">
                          <p className="text-sm font-bold text-slate-800 font-mono">{c.codigo}</p>
                          <p className="text-[10px] text-slate-400">
                            {c.nome_projeto || 'Sem projeto'} · {new Date(c.created_at).toLocaleDateString('pt-BR')}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <span className={`text-[10px] font-bold px-2 py-1 rounded-full uppercase ${STATUS_BADGE[c.status] || STATUS_BADGE.rascunho}`}>
                            {c.status}
                          </span>
                          <button onClick={() => baixarExcel(c)} title="Baixar planilha"
                            className="text-xs px-3 py-1.5 bg-white border border-slate-200 rounded-lg font-bold text-slate-600 hover:border-amber-400 hover:text-amber-600 transition-all">
                            📥
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
};

export default PainelCotacoes;
