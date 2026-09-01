import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import api from '../api';
import PropostaComercial from './PropostaComercial';

/**
 * Painel de Cotações (Fase 2).
 *
 * - Lista as cotações do usuário com status
 * - Importa a cotação devolvida pelo fornecedor, por dois caminhos:
 *     (a) planilha Excel: upload → análise (nada gravado) → conferência → confirmar
 *     (b) PDF no formato próprio do fornecedor: upload → IA casa com nossos itens
 *         (mesmo relatório de conferência) → confirmar. Ver
 *         DESIGN_IMPORTACAO_PDF_COTACAO_2026-09-01.md.
 */
const STATUS_BADGE = {
  rascunho:   'bg-slate-100 text-slate-600',
  enviada:    'bg-amber-100 text-amber-700',
  recebida:   'bg-blue-100 text-blue-700',
  processada: 'bg-emerald-100 text-emerald-700',
  cancelada:  'bg-red-100 text-red-500',
};

const ITEM_STATUS = {
  ok:                    { cor: 'bg-emerald-50 border-emerald-200', label: '✅ Preço lido',           txt: 'text-emerald-700' },
  sem_preco:             { cor: 'bg-amber-50 border-amber-200',     label: '⚠️ Sem preço',            txt: 'text-amber-700' },
  preco_invalido:        { cor: 'bg-red-50 border-red-200',         label: '❌ Preço ilegível',       txt: 'text-red-600' },
  nao_encontrado:        { cor: 'bg-red-50 border-red-200',         label: '❌ Não encontrado',       txt: 'text-red-600' },
  linha_extra:           { cor: 'bg-blue-50 border-blue-200',       label: 'ℹ️ Linha extra',          txt: 'text-blue-600' },
  possivel_substituicao: { cor: 'bg-violet-50 border-violet-200',   label: '🔄 Possível substituição', txt: 'text-violet-700' },
};

const RESUMO_LABELS = {
  ok: 'com preço',
  sem_preco: 'sem preço',
  preco_invalido: 'ilegíveis',
  nao_encontrado: 'não encontrados',
  possivel_substituicao: 'possível substituição',
  linha_extra: 'linhas extras',
};

const PROPOSTA_BADGE = {
  rascunho: 'bg-slate-100 text-slate-600',
  enviada:  'bg-amber-100 text-amber-700',
  aceita:   'bg-emerald-100 text-emerald-700',
  recusada: 'bg-red-100 text-red-500',
};

const PainelCotacoes = ({ aberto, aoFechar, projetoAtual = null, onGerarProposta }) => {
  const [cotacoes, setCotacoes] = useState([]);
  const [propostas, setPropostas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState('');
  const [filtroProjeto, setFiltroProjeto] = useState(true); // true = só projeto atual

  // Fluxo de importação
  const [analise, setAnalise] = useState(null);       // resultado do /analisar
  const [edicao, setEdicao] = useState({});           // { item_id: { preco, marca, prazo, obs } }
  const [importando, setImportando] = useState(false);
  const [sucessoImport, setSucessoImport] = useState(null);
  const [propostaVer, setPropostaVer] = useState(null);   // proposta salva aberta para visualização
  const fileRef = useRef(null);
  const fileRefPdf = useRef(null);
  const [cotacaoPdfAlvo, setCotacaoPdfAlvo] = useState(null);   // cotação escolhida antes de abrir o seletor de PDF

  useEffect(() => {
    if (aberto) {
      setErro(''); setAnalise(null); setSucessoImport(null);
      // Se tem projeto aberto, começa filtrado por ele; senão mostra tudo
      setFiltroProjeto(!!projetoAtual?.id);
      carregar();
    }
  }, [aberto]);

  const carregar = async () => {
    setLoading(true);
    try {
      const [rc, rp] = await Promise.all([
        api.get('/api/v1/cotacoes'),
        api.get('/api/v1/propostas'),
      ]);
      setCotacoes(rc.data);
      setPropostas(rp.data);
    } catch {
      setErro('Erro ao carregar cotações.');
    } finally {
      setLoading(false);
    }
  };

  const temProjeto = !!projetoAtual?.id;
  const cotacoesFiltradas = temProjeto && filtroProjeto
    ? cotacoes.filter(c => c.projeto_id === projetoAtual.id)
    : cotacoes;
  const propostasFiltradas = temProjeto && filtroProjeto
    ? propostas.filter(p => p.projeto_id === projetoAtual.id)
    : propostas;

  const mudarStatusProposta = async (prop, novoStatus) => {
    try {
      await api.patch(`/api/v1/propostas/${prop.id}`, { status: novoStatus });
      carregar();
    } catch { setErro('Erro ao atualizar o status da proposta.'); }
  };

  const excluirProposta = async (prop) => {
    if (!window.confirm(`Excluir a proposta ${prop.codigo}?`)) return;
    try {
      await api.delete(`/api/v1/propostas/${prop.id}`);
      carregar();
    } catch { setErro('Erro ao excluir a proposta.'); }
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

  // Cotação em PDF (formato do fornecedor) — casamento por IA. Diferente da planilha,
  // o PDF não se autoidentifica, então a cotação-alvo já foi escolhida (cotacaoPdfAlvo)
  // antes de abrir o seletor de arquivo.
  const analisarPdf = async (file) => {
    if (!file || !cotacaoPdfAlvo) return;
    setImportando(true); setErro(''); setSucessoImport(null);
    try {
      const form = new FormData();
      form.append('arquivo', file);
      const r = await api.post(`/api/v1/cotacoes/${cotacaoPdfAlvo}/importar/analisar-pdf`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setAnalise(r.data);
      const ed = {};
      r.data.itens.forEach(it => {
        if (it.item_id) {
          ed[it.item_id] = {
            preco: it.preco_unitario ?? '',
            marca: it.marca_modelo ?? '',
            prazo: it.prazo_dias ?? '',
            obs: it.obs ?? '',
            termoFornecedor: it.termo_fornecedor ?? null,
          };
        }
      });
      setEdicao(ed);
    } catch (e) {
      setErro(e.response?.data?.detail || 'Erro ao analisar o PDF.');
    } finally {
      setImportando(false);
      setCotacaoPdfAlvo(null);
      if (fileRefPdf.current) fileRefPdf.current.value = '';
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
        termo_fornecedor: e.termoFornecedor || null,
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
          <div>
            <h3 className="text-white font-bold flex items-center gap-2">📊 Cotações</h3>
            {temProjeto && (
              <p className="text-slate-400 text-[11px] mt-0.5 truncate max-w-xs">
                {projetoAtual.nome || 'Projeto sem nome'}
              </p>
            )}
          </div>
          <div className="flex items-center gap-3">
            {temProjeto && (
              <div className="flex items-center bg-slate-800 rounded-lg p-0.5 text-xs font-bold">
                <button
                  onClick={() => setFiltroProjeto(true)}
                  className={`px-3 py-1.5 rounded-md transition-colors ${filtroProjeto ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'}`}>
                  Este projeto
                </button>
                <button
                  onClick={() => setFiltroProjeto(false)}
                  className={`px-3 py-1.5 rounded-md transition-colors ${!filtroProjeto ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'}`}>
                  Todas
                </button>
              </div>
            )}
            <button onClick={aoFechar} className="text-white/60 hover:text-white text-xl leading-none">✕</button>
          </div>
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
                  {Object.entries(analise.resumo)
                    .filter(([, v]) => v > 0)
                    .map(([k, v]) => `${v} ${RESUMO_LABELS[k] || k}`)
                    .join(' · ')}
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
                      {it.status === 'possivel_substituicao' && (
                        <p className="text-[10px] text-violet-600 mb-2">
                          A IA achou algo relacionado, mas não exatamente o que foi pedido — confira antes de aceitar.
                          {it.obs && <><br />{it.obs}</>}
                        </p>
                      )}
                      {it.descricao_pdf && it.status !== 'linha_extra' && (
                        <p className="text-[10px] text-slate-400 italic mb-2">
                          Lido no PDF: "{it.descricao_pdf}"
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
                  Fornecedor devolveu no PDF próprio da loja, sem preencher a planilha? Use "Importar PDF" na
                  cotação específica, na lista abaixo.
                </p>
                <input ref={fileRef} type="file" accept=".xlsx,.xlsm" className="hidden"
                  onChange={e => analisarArquivo(e.target.files[0])} />
                <input ref={fileRefPdf} type="file" accept=".pdf" className="hidden"
                  onChange={e => analisarPdf(e.target.files[0])} />
                <button onClick={() => fileRef.current?.click()} disabled={importando}
                  className="px-6 py-2.5 bg-amber-500 hover:bg-amber-600 text-white rounded-xl font-bold text-sm shadow transition-all disabled:opacity-40">
                  {importando ? 'Analisando...' : 'SELECIONAR ARQUIVO EXCEL'}
                </button>
              </div>

              {/* ── Gerar proposta (navega para Card 6) ── */}
              <div className={`rounded-xl border p-5 flex items-center justify-between gap-4 ${
                cotacoesFiltradas.some(c => c.status === 'processada')
                  ? 'bg-indigo-50 border-indigo-200'
                  : 'bg-amber-50 border-amber-200'
              }`}>
                <div>
                  {cotacoesFiltradas.some(c => c.status === 'processada') ? (
                    <>
                      <p className="text-sm font-bold text-indigo-900">💼 Pronto para fechar negócio?</p>
                      <p className="text-xs text-indigo-600 mt-0.5">
                        Cotação validada — clique para gerar a proposta técnica comercial no projeto.
                      </p>
                    </>
                  ) : cotacoesFiltradas.some(c => c.status !== 'cancelada') ? (
                    <>
                      <p className="text-sm font-bold text-amber-800">⏳ Aguardando retorno do fornecedor</p>
                      <p className="text-xs text-amber-700 mt-0.5">
                        Importe a planilha devolvida pelo fornecedor e confirme os preços para liberar a proposta.
                      </p>
                    </>
                  ) : (
                    <>
                      <p className="text-sm font-bold text-amber-800">📋 Nenhuma cotação processada</p>
                      <p className="text-xs text-amber-700 mt-0.5">
                        Gere uma planilha de cotação no card de Orçamento, envie ao fornecedor e importe os preços aqui.
                      </p>
                    </>
                  )}
                </div>
                {onGerarProposta && (
                  <button
                    onClick={() => { aoFechar(); onGerarProposta(); }}
                    className={`px-5 py-2.5 rounded-xl font-bold text-sm shadow transition-all whitespace-nowrap text-white ${
                      cotacoesFiltradas.some(c => c.status === 'processada')
                        ? 'bg-indigo-600 hover:bg-indigo-700'
                        : 'bg-amber-500 hover:bg-amber-600'
                    }`}>
                    {cotacoesFiltradas.some(c => c.status === 'processada') ? 'GERAR PROPOSTA →' : 'IR PARA O PROJETO →'}
                  </button>
                )}
              </div>

              {/* ── Propostas salvas ── */}
              {propostasFiltradas.length > 0 && (
                <div>
                  <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3">💼 Propostas comerciais</h4>
                  <div className="space-y-2">
                    {propostasFiltradas.map(p => (
                      <div key={p.id} className="flex items-center justify-between gap-3 p-3 bg-indigo-50/50 rounded-xl border border-indigo-100 hover:border-indigo-300 transition-all">
                        <div className="min-w-0 cursor-pointer" onClick={() => setPropostaVer(p)} title="Abrir proposta">
                          <p className="text-sm font-bold text-indigo-700 font-mono hover:underline">{p.codigo} 📄</p>
                          <p className="text-[10px] text-slate-400">
                            {p.dados?.cliente?.nome || 'Sem cliente'} · R$ {(p.dados?.valores?.preco_venda || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            {' · '}{new Date(p.created_at).toLocaleDateString('pt-BR')}
                            {' · '}{p.dados?.modo === 'venda_direta' ? 'venda direta' : 'empreitada'}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <select value={p.status} onChange={e => mudarStatusProposta(p, e.target.value)}
                            className={`text-[10px] font-bold px-2 py-1 rounded-full uppercase border-0 cursor-pointer ${PROPOSTA_BADGE[p.status] || PROPOSTA_BADGE.rascunho}`}>
                            <option value="rascunho">rascunho</option>
                            <option value="enviada">enviada</option>
                            <option value="aceita">✓ aceita</option>
                            <option value="recusada">recusada</option>
                          </select>
                          <button onClick={() => excluirProposta(p)} title="Excluir"
                            className="text-xs px-2 py-1.5 text-slate-300 hover:text-red-400 transition-colors">✕</button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Lista de cotações ── */}
              <div>
                <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3">
                  Cotações geradas
                  {temProjeto && filtroProjeto && cotacoesFiltradas.length === 0 && cotacoes.length > 0 && (
                    <span className="ml-2 text-indigo-400 font-normal normal-case">
                      — nenhuma neste projeto
                      <button onClick={() => setFiltroProjeto(false)} className="ml-1 underline hover:text-indigo-300">ver todas</button>
                    </span>
                  )}
                </h4>
                {loading ? (
                  <p className="text-sm text-slate-400 animate-pulse">Carregando...</p>
                ) : cotacoesFiltradas.length === 0 ? (
                  <p className="text-sm text-slate-400 italic">
                    {temProjeto && filtroProjeto
                      ? 'Nenhuma cotação para este projeto ainda. Gere uma no card de Orçamento.'
                      : 'Nenhuma cotação ainda. Gere uma no card de Orçamento do seu projeto.'}
                  </p>
                ) : (
                  <div className="space-y-2">
                    {cotacoesFiltradas.map(c => (
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
                          {c.status !== 'cancelada' && (
                            <button
                              onClick={() => { setCotacaoPdfAlvo(c.id); fileRefPdf.current?.click(); }}
                              disabled={importando}
                              title="Importar cotação em PDF (formato do fornecedor)"
                              className="text-[10px] px-3 py-1.5 bg-white border border-slate-200 rounded-lg font-bold text-slate-600 hover:border-violet-400 hover:text-violet-600 transition-all disabled:opacity-40">
                              📄 Importar PDF
                            </button>
                          )}
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

      <PropostaComercial aberto={!!propostaVer} propostaVisualizar={propostaVer} aoFechar={() => setPropostaVer(null)} />
    </div>,
    document.body
  );
};

export default PainelCotacoes;
