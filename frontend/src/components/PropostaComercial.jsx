import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import api from '../api';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

/**
 * Fase 3 — Proposta Comercial a partir das cotações processadas.
 *
 * Passos:
 *   1. Fonte de preços  — comparativo entre fornecedores (cotação única ou melhores preços)
 *   2. Composição       — mão de obra, locomoção, despesas, margem, impostos, modo de venda
 *   3. Condições        — pagamento, validade, prazo, garantia, escopo, dados do cliente
 *   4. Preview          — proposta formatada com bloco de aceite + PDF + salvar
 */

const fmt = (v) => (v ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const BLOCO_DE = (tipo) => {
  const t = (tipo || '').toLowerCase();
  if (t.includes('equipamento') || t.includes('condensadora') || t.includes('evaporadora') || t.includes('componente'))
    return 'Sistema de refrigeração';
  return 'Painéis, estrutura e materiais';
};

const CONDICOES_PADRAO = {
  pagamento: '40% na aprovação do pedido · 40% na entrega dos materiais · 20% na entrega técnica',
  validade_dias: 10,
  prazo_execucao: '30 dias corridos após confirmação do pedido',
  garantia: '12 meses para os serviços de instalação. Equipamentos: garantia de fábrica do fabricante.',
  incluso: 'Fornecimento e montagem dos painéis frigoríficos; instalação do sistema de refrigeração; tubulações frigorígenas e elétricas entre evaporador e unidade condensadora; vácuo, carga de fluido e entrega técnica com câmara em temperatura.',
  nao_incluso: 'Obras civis e base nivelada; alimentação elétrica até o ponto da unidade condensadora; disjuntores e quadro geral; descarte de entulho; taxas e licenças.',
};

const PropostaComercial = ({ aberto, aoFechar }) => {
  const previewRef = useRef(null);

  const [passo, setPasso] = useState(1);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState('');

  // Passo 1 — fonte de preços
  const [comparativo, setComparativo] = useState(null);
  const [fonte, setFonte] = useState('melhores');        // 'melhores' | codigo da cotação

  // Passo 2 — composição
  const [custos, setCustos] = useState({ mao_obra: '', locomocao: '', despesas: '', outros: '' });
  const [modo, setModo] = useState('empreitada');         // 'empreitada' | 'venda_direta'
  const [margem, setMargem] = useState(25);
  const [imposto, setImposto] = useState(6);
  const [apresentacao, setApresentacao] = useState('blocos');  // 'blocos' | 'global'

  // Passo 3 — condições e cliente
  const [cond, setCond] = useState(CONDICOES_PADRAO);
  const [cliente, setCliente] = useState({ nome: '', cnpj: '', contato: '' });
  const [resumoObjeto, setResumoObjeto] = useState('Fornecimento e instalação de câmara frigorífica completa, conforme dimensionamento técnico.');

  // Passo 4
  const [codigoSalvo, setCodigoSalvo] = useState(null);

  useEffect(() => {
    if (aberto) {
      setPasso(1); setErro(''); setCodigoSalvo(null);
      carregarComparativo();
    }
  }, [aberto]);

  const carregarComparativo = async () => {
    setLoading(true);
    try {
      const r = await api.get('/api/v1/propostas/comparativo');
      setComparativo(r.data);
      if (r.data.cotacoes.length === 1) setFonte(r.data.cotacoes[0].codigo);
    } catch {
      setErro('Erro ao carregar o comparativo de cotações.');
    } finally {
      setLoading(false);
    }
  };

  // ── Cálculos ────────────────────────────────────────────────────────────
  const itensComPreco = () => {
    if (!comparativo) return [];
    return comparativo.itens.map(it => {
      let preco = null, fornecedor = null;
      if (fonte === 'melhores') {
        if (it.melhor) { preco = it.melhor.preco_unitario; fornecedor = it.melhor.fornecedor; }
      } else {
        const p = it.precos[fonte];
        if (p?.preco_unitario) { preco = p.preco_unitario; fornecedor = p.fornecedor; }
      }
      return { ...it, preco_unitario: preco, fornecedor, total: preco ? preco * it.qtde : null };
    });
  };

  const calc = () => {
    const itens = itensComPreco();
    const custo_materiais = itens.reduce((s, i) => s + (i.total || 0), 0);
    const semPreco = itens.filter(i => !i.preco_unitario).length;

    const n = (v) => parseFloat(v) || 0;
    const custo_servicos = n(custos.mao_obra) + n(custos.locomocao) + n(custos.despesas) + n(custos.outros);
    const taxa = (parseFloat(margem) || 0) + (parseFloat(imposto) || 0);
    const fator = taxa < 99 ? 1 / (1 - taxa / 100) : 1;

    let preco_venda, preco_materiais_cliente, preco_servicos_cliente;
    if (modo === 'venda_direta') {
      // Materiais: repasse direto do fornecedor. Margem só sobre serviços.
      preco_servicos_cliente = custo_servicos * fator;
      preco_materiais_cliente = custo_materiais;
      preco_venda = preco_materiais_cliente + preco_servicos_cliente;
    } else {
      const custo_total = custo_materiais + custo_servicos;
      preco_venda = custo_total * fator;
      preco_servicos_cliente = custo_servicos * fator;
      preco_materiais_cliente = preco_venda - preco_servicos_cliente;
    }

    // Blocos para apresentação (empreitada)
    const blocos = {};
    itens.forEach(i => {
      if (!i.total) return;
      const b = BLOCO_DE(i.tipo_item);
      blocos[b] = (blocos[b] || 0) + i.total;
    });
    const blocosCliente = Object.entries(blocos).map(([nome, custo]) => ({
      nome,
      valor: modo === 'venda_direta' ? custo : custo * fator,
    }));
    blocosCliente.push({ nome: 'Instalação, mobilização e comissionamento', valor: preco_servicos_cliente });

    const custo_total = custo_materiais + custo_servicos;

    // Faturamento próprio: na venda direta os materiais são faturados pelo
    // fornecedor — impostos e lucro incidem APENAS sobre os serviços.
    const faturamento_proprio = modo === 'venda_direta' ? preco_servicos_cliente : preco_venda;
    const custo_proprio       = modo === 'venda_direta' ? custo_servicos : custo_total;
    const impostos_valor      = faturamento_proprio * ((parseFloat(imposto) || 0) / 100);
    const lucro_liquido       = faturamento_proprio - custo_proprio - impostos_valor;

    return {
      itens, semPreco, custo_materiais, custo_servicos, custo_total,
      preco_venda, preco_materiais_cliente, preco_servicos_cliente,
      faturamento_proprio, impostos_valor, lucro_liquido,
      blocosCliente,
    };
  };

  const c = comparativo ? calc() : null;

  // Fornecedores usados (para venda direta)
  const fornecedoresUsados = c
    ? [...new Set(c.itens.filter(i => i.fornecedor).map(i => i.fornecedor))]
    : [];

  // ── Salvar e PDF ────────────────────────────────────────────────────────
  const salvarProposta = async () => {
    setLoading(true); setErro('');
    try {
      const dados = {
        fonte, modo, apresentacao,
        margem_perc: parseFloat(margem) || 0,
        imposto_perc: parseFloat(imposto) || 0,
        custos: { ...custos },
        condicoes: { ...cond },
        cliente: { ...cliente },
        resumo_objeto: resumoObjeto,
        valores: {
          custo_materiais: c.custo_materiais,
          custo_servicos: c.custo_servicos,
          preco_venda: c.preco_venda,
          faturamento_proprio: c.faturamento_proprio,
          impostos_valor: c.impostos_valor,
          lucro_liquido: c.lucro_liquido,
          blocos: c.blocosCliente,
        },
        itens: c.itens.map(i => ({
          descricao: i.descricao, qtde: i.qtde, unidade: i.unidade,
          preco_unitario: i.preco_unitario, fornecedor: i.fornecedor,
        })),
      };
      const r = await api.post('/api/v1/propostas', { dados });
      setCodigoSalvo(r.data.codigo);
    } catch {
      setErro('Erro ao salvar a proposta.');
    } finally {
      setLoading(false);
    }
  };

  const gerarPDF = async () => {
    if (!previewRef.current) return;
    setLoading(true);
    try {
      const canvas = await html2canvas(previewRef.current, { scale: 2, useCORS: true, logging: false });
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pw = pdf.internal.pageSize.getWidth();
      const ph = pdf.internal.pageSize.getHeight();
      const ch = (canvas.height * pw) / canvas.width;
      let left = ch, pos = 0;
      pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, pos, pw, ch);
      left -= ph;
      while (left >= 0) { pos = left - ch; pdf.addPage(); pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, pos, pw, ch); left -= ph; }
      pdf.save(`Proposta_${cliente.nome?.replace(/\s+/g, '_') || 'Camara'}.pdf`);
    } catch { setErro('Erro ao gerar PDF.'); }
    finally { setLoading(false); }
  };

  if (!aberto) return null;

  const validadeData = new Date(Date.now() + (parseInt(cond.validade_dias) || 10) * 86400000);

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden">

        {/* Header com passos */}
        <div className="bg-indigo-700 px-6 py-4 flex items-center justify-between flex-shrink-0">
          <div>
            <h3 className="text-white font-bold">💼 Proposta Comercial</h3>
            <div className="flex gap-2 mt-1">
              {['Preços', 'Composição', 'Condições', 'Proposta'].map((l, i) => (
                <span key={l} className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${passo === i + 1 ? 'bg-white text-indigo-700' : passo > i + 1 ? 'bg-indigo-500 text-white' : 'bg-indigo-900/40 text-indigo-300'}`}>
                  {i + 1}. {l}
                </span>
              ))}
            </div>
          </div>
          <button onClick={aoFechar} className="text-white/60 hover:text-white text-xl leading-none">✕</button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {erro && <p className="text-sm text-red-600 font-bold bg-red-50 rounded-lg px-3 py-2 border border-red-200 mb-4">{erro}</p>}
          {loading && !comparativo && <p className="text-sm text-slate-400 animate-pulse">Carregando comparativo...</p>}

          {/* ══ PASSO 1 — FONTE DE PREÇOS ══ */}
          {passo === 1 && comparativo && (
            comparativo.cotacoes.length === 0 ? (
              <div className="text-center py-10 text-slate-400">
                <p className="font-bold">Nenhuma cotação processada ainda.</p>
                <p className="text-xs mt-2">Importe a resposta de pelo menos um fornecedor no painel de Cotações.</p>
              </div>
            ) : (
              <div className="space-y-5">
                <div>
                  <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3">De onde vêm os preços dos materiais?</h4>
                  <div className="space-y-2">
                    {comparativo.cotacoes.length > 1 && (
                      <label className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all ${fonte === 'melhores' ? 'bg-emerald-50 border-emerald-300' : 'bg-slate-50 border-slate-200'}`}>
                        <input type="radio" checked={fonte === 'melhores'} onChange={() => setFonte('melhores')} className="accent-emerald-600" />
                        <div className="flex-1">
                          <p className="text-sm font-bold text-slate-800">🏆 Melhores preços (mix de fornecedores)</p>
                          <p className="text-[10px] text-slate-500">Cada item pelo menor preço entre as cotações</p>
                        </div>
                        <span className="font-black text-emerald-700">R$ {fmt(comparativo.totais.melhores_precos)}</span>
                      </label>
                    )}
                    {comparativo.totais.por_cotacao.map(t => {
                      const cab = comparativo.cotacoes.find(x => x.codigo === t.codigo);
                      return (
                        <label key={t.codigo} className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all ${fonte === t.codigo ? 'bg-indigo-50 border-indigo-300' : 'bg-slate-50 border-slate-200'}`}>
                          <input type="radio" checked={fonte === t.codigo} onChange={() => setFonte(t.codigo)} className="accent-indigo-600" />
                          <div className="flex-1">
                            <p className="text-sm font-bold text-slate-800">{cab?.fornecedor}</p>
                            <p className="text-[10px] text-slate-500 font-mono">{t.codigo} {!t.completa && '· ⚠️ itens sem preço'}</p>
                          </div>
                          <span className="font-black text-slate-700">R$ {fmt(t.total)}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>

                {/* Tabela comparativa */}
                <div className="bg-slate-50 rounded-xl border border-slate-200 overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-slate-200">
                        <th className="text-left p-2 font-bold text-slate-500">Item</th>
                        {comparativo.cotacoes.map(cab => (
                          <th key={cab.codigo} className="text-right p-2 font-bold text-slate-500">{cab.fornecedor}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {comparativo.itens.map((it, i) => (
                        <tr key={i} className="border-b border-slate-100 last:border-0">
                          <td className="p-2 text-slate-700">{it.descricao} <span className="text-slate-400">×{it.qtde}</span></td>
                          {comparativo.cotacoes.map(cab => {
                            const p = it.precos[cab.codigo]?.preco_unitario;
                            const ehMelhor = it.melhor?.codigo === cab.codigo;
                            return (
                              <td key={cab.codigo} className={`p-2 text-right font-bold ${ehMelhor ? 'text-emerald-600' : p ? 'text-slate-600' : 'text-slate-300'}`}>
                                {p ? `${ehMelhor ? '🏆 ' : ''}R$ ${fmt(p)}` : '—'}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="flex justify-end">
                  <button onClick={() => setPasso(2)} className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-sm shadow transition-all">
                    Continuar ➡️
                  </button>
                </div>
              </div>
            )
          )}

          {/* ══ PASSO 2 — COMPOSIÇÃO ══ */}
          {passo === 2 && c && (
            <div className="space-y-5">
              <div className="bg-slate-50 rounded-xl px-4 py-3 border border-slate-200 flex justify-between items-center">
                <span className="text-sm text-slate-600">Custo dos materiais (cotação)</span>
                <span className="font-black text-slate-800">R$ {fmt(c.custo_materiais)}</span>
              </div>
              {c.semPreco > 0 && (
                <p className="text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-2 border border-amber-200 font-bold">
                  ⚠️ {c.semPreco} item(ns) sem preço na fonte escolhida — não entram no total.
                </p>
              )}

              <div>
                <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3">Seus custos de serviço</h4>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    ['mao_obra', 'Mão de obra (instalação)'],
                    ['locomocao', 'Locomoção / mobilização'],
                    ['despesas', 'Despesas gerais'],
                    ['outros', 'Outros'],
                  ].map(([k, label]) => (
                    <div key={k}>
                      <label className="text-[10px] font-bold text-slate-500 uppercase">{label}</label>
                      <div className="relative">
                        <span className="absolute left-3 top-2 text-slate-400 text-sm">R$</span>
                        <input type="number" min="0" step="0.01" value={custos[k]}
                          onChange={e => setCustos(p => ({ ...p, [k]: e.target.value }))}
                          placeholder="0,00"
                          className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-300 text-sm outline-none focus:ring-2 focus:ring-indigo-400" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Modo de venda</h4>
                  <div className="space-y-2">
                    <label className={`flex items-start gap-2 p-3 rounded-xl border cursor-pointer text-xs ${modo === 'empreitada' ? 'bg-indigo-50 border-indigo-300' : 'bg-slate-50 border-slate-200'}`}>
                      <input type="radio" checked={modo === 'empreitada'} onChange={() => setModo('empreitada')} className="accent-indigo-600 mt-0.5" />
                      <span><b>Empreitada (faturado)</b><br /><span className="text-slate-500">Preço único com margem embutida em tudo</span></span>
                    </label>
                    <label className={`flex items-start gap-2 p-3 rounded-xl border cursor-pointer text-xs ${modo === 'venda_direta' ? 'bg-indigo-50 border-indigo-300' : 'bg-slate-50 border-slate-200'}`}>
                      <input type="radio" checked={modo === 'venda_direta'} onChange={() => setModo('venda_direta')} className="accent-indigo-600 mt-0.5" />
                      <span><b>Venda direta</b><br /><span className="text-slate-500">Cliente compra materiais do fornecedor; margem só nos serviços</span></span>
                    </label>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="text-[10px] font-bold text-slate-500 uppercase">Margem de lucro (% sobre venda)</label>
                    <input type="number" min="0" max="80" value={margem} onChange={e => setMargem(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-slate-500 uppercase">Impostos (% sobre venda)</label>
                    <input type="number" min="0" max="40" value={imposto} onChange={e => setImposto(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-slate-500 uppercase">Apresentação ao cliente</label>
                    <select value={apresentacao} onChange={e => setApresentacao(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none">
                      <option value="blocos">Valores por bloco (recomendado)</option>
                      <option value="global">Valor global único</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Resumo financeiro privado */}
              <div className="bg-slate-900 rounded-xl p-4 text-white">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">🔒 Resumo financeiro — privado (não vai ao cliente)</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                  <div><p className="text-[10px] text-slate-400">{modo === 'venda_direta' ? 'Custo dos serviços' : 'Custo total'}</p><p className="font-black">R$ {fmt(modo === 'venda_direta' ? c.custo_servicos : c.custo_total)}</p></div>
                  <div><p className="text-[10px] text-slate-400">Seu faturamento</p><p className="font-black text-emerald-400">R$ {fmt(c.faturamento_proprio)}</p></div>
                  <div><p className="text-[10px] text-slate-400">Impostos ({imposto}%)</p><p className="font-black text-amber-400">R$ {fmt(c.impostos_valor)}</p></div>
                  <div><p className="text-[10px] text-slate-400">Lucro líquido</p><p className="font-black text-emerald-400">R$ {fmt(c.lucro_liquido)}</p></div>
                </div>
                {modo === 'venda_direta' && (
                  <p className="text-[10px] text-slate-400 mt-2">
                    Venda direta: materiais R$ {fmt(c.preco_materiais_cliente)} faturados direto pelo fornecedor (fora do seu faturamento — sem impostos para você) · seus serviços R$ {fmt(c.preco_servicos_cliente)}
                  </p>
                )}
              </div>

              <div className="flex justify-between">
                <button onClick={() => setPasso(1)} className="px-4 py-2 text-slate-500 font-bold text-sm">⬅️ Voltar</button>
                <button onClick={() => setPasso(3)} className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-sm shadow transition-all">
                  Continuar ➡️
                </button>
              </div>
            </div>
          )}

          {/* ══ PASSO 3 — CONDIÇÕES ══ */}
          {passo === 3 && (
            <div className="space-y-5">
              <div>
                <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3">Dados do cliente</h4>
                <div className="grid grid-cols-3 gap-3">
                  <input value={cliente.nome} placeholder="Nome / Razão Social"
                    onChange={e => setCliente(p => ({ ...p, nome: e.target.value }))}
                    className="px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
                  <input value={cliente.cnpj} placeholder="CNPJ / CPF"
                    onChange={e => setCliente(p => ({ ...p, cnpj: e.target.value }))}
                    className="px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
                  <input value={cliente.contato} placeholder="Contato"
                    onChange={e => setCliente(p => ({ ...p, contato: e.target.value }))}
                    className="px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Objeto da proposta (resumo executivo)</label>
                <textarea value={resumoObjeto} onChange={e => setResumoObjeto(e.target.value)} rows={2}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">✅ Escopo incluído</label>
                  <textarea value={cond.incluso} onChange={e => setCond(p => ({ ...p, incluso: e.target.value }))} rows={4}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs outline-none" />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">❌ Não incluído</label>
                  <textarea value={cond.nao_incluso} onChange={e => setCond(p => ({ ...p, nao_incluso: e.target.value }))} rows={4}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs outline-none" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Condições de pagamento</label>
                  <input value={cond.pagamento} onChange={e => setCond(p => ({ ...p, pagamento: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Prazo de execução</label>
                  <input value={cond.prazo_execucao} onChange={e => setCond(p => ({ ...p, prazo_execucao: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Validade da proposta (dias)</label>
                  <input type="number" min="1" value={cond.validade_dias}
                    onChange={e => setCond(p => ({ ...p, validade_dias: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Garantia</label>
                  <input value={cond.garantia} onChange={e => setCond(p => ({ ...p, garantia: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
                </div>
              </div>

              <div className="flex justify-between">
                <button onClick={() => setPasso(2)} className="px-4 py-2 text-slate-500 font-bold text-sm">⬅️ Voltar</button>
                <button onClick={() => setPasso(4)} className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-sm shadow transition-all">
                  Ver proposta ➡️
                </button>
              </div>
            </div>
          )}

          {/* ══ PASSO 4 — PREVIEW DA PROPOSTA ══ */}
          {passo === 4 && c && (
            <div className="space-y-4">
              {codigoSalvo && (
                <p className="text-sm text-emerald-700 font-bold bg-emerald-50 rounded-lg px-3 py-2 border border-emerald-200">
                  ✅ Proposta {codigoSalvo} salva! Histórico disponível para acompanhamento do aceite.
                </p>
              )}

              {/* Documento */}
              <div ref={previewRef} className="bg-white border-2 border-slate-900 rounded-xl overflow-hidden">
                {/* Cabeçalho */}
                <div className="bg-slate-900 text-white p-6 flex justify-between items-start">
                  <div>
                    <h3 className="text-xl font-black tracking-tight">PROPOSTA TÉCNICA COMERCIAL</h3>
                    <p className="text-slate-400 text-[10px] font-bold uppercase tracking-widest mt-1">Engenharia de Refrigeração</p>
                  </div>
                  <div className="text-right text-xs">
                    <p className="font-bold">{new Date().toLocaleDateString('pt-BR')}</p>
                    <p className="text-slate-400">Validade: {validadeData.toLocaleDateString('pt-BR')}</p>
                  </div>
                </div>

                <div className="p-6 space-y-6">
                  {/* Cliente + objeto */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                      <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Cliente</p>
                      <p className="font-black text-slate-900">{cliente.nome || '—'}</p>
                      <p className="text-xs text-slate-500">{cliente.cnpj}{cliente.contato ? ` · A/C ${cliente.contato}` : ''}</p>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                      <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Objeto</p>
                      <p className="text-xs text-slate-700 leading-relaxed">{resumoObjeto}</p>
                    </div>
                  </div>

                  {/* Escopo */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-[9px] font-black text-emerald-600 uppercase tracking-widest mb-2 border-b border-emerald-100 pb-1">✅ Escopo incluído</p>
                      <p className="text-[11px] text-slate-600 leading-relaxed whitespace-pre-line">{cond.incluso}</p>
                    </div>
                    <div>
                      <p className="text-[9px] font-black text-red-400 uppercase tracking-widest mb-2 border-b border-red-100 pb-1">❌ Não incluído</p>
                      <p className="text-[11px] text-slate-600 leading-relaxed whitespace-pre-line">{cond.nao_incluso}</p>
                    </div>
                  </div>

                  {/* Investimento */}
                  <div>
                    <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-3 border-b border-slate-100 pb-1">💰 Investimento</p>

                    {modo === 'venda_direta' ? (
                      <div className="space-y-2">
                        <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg border border-blue-100">
                          <div>
                            <p className="text-sm font-bold text-slate-800">Materiais e equipamentos</p>
                            <p className="text-[10px] text-slate-500">
                              Faturamento direto: {fornecedoresUsados.join(', ') || 'fornecedor'} — pagamento do cliente ao fornecedor
                            </p>
                          </div>
                          <span className="font-black text-slate-800 whitespace-nowrap">R$ {fmt(c.preco_materiais_cliente)}</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-indigo-50 rounded-lg border border-indigo-100">
                          <p className="text-sm font-bold text-slate-800">Serviços de instalação e comissionamento</p>
                          <span className="font-black text-slate-800 whitespace-nowrap">R$ {fmt(c.preco_servicos_cliente)}</span>
                        </div>
                      </div>
                    ) : apresentacao === 'blocos' ? (
                      <div className="space-y-2">
                        {c.blocosCliente.filter(b => b.valor > 0).map(b => (
                          <div key={b.nome} className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                            <p className="text-sm font-bold text-slate-700">{b.nome}</p>
                            <span className="font-black text-slate-800 whitespace-nowrap">R$ {fmt(b.valor)}</span>
                          </div>
                        ))}
                      </div>
                    ) : null}

                    <div className="flex justify-between items-center mt-3 pt-3 border-t-2 border-slate-900">
                      <p className="font-black text-slate-900 uppercase text-sm">Investimento total</p>
                      <p className="text-2xl font-black text-indigo-700">R$ {fmt(c.preco_venda)}</p>
                    </div>
                  </div>

                  {/* Condições comerciais */}
                  <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 grid grid-cols-2 gap-3 text-[11px]">
                    <div><p className="font-black text-slate-500 text-[9px] uppercase">Pagamento</p><p className="text-slate-700">{cond.pagamento}</p></div>
                    <div><p className="font-black text-slate-500 text-[9px] uppercase">Prazo de execução</p><p className="text-slate-700">{cond.prazo_execucao}</p></div>
                    <div><p className="font-black text-slate-500 text-[9px] uppercase">Garantia</p><p className="text-slate-700">{cond.garantia}</p></div>
                    <div><p className="font-black text-slate-500 text-[9px] uppercase">Validade</p><p className="text-slate-700">{cond.validade_dias} dias — até {validadeData.toLocaleDateString('pt-BR')}</p></div>
                  </div>

                  {/* Bloco de aceite */}
                  <div className="border-2 border-dashed border-slate-300 rounded-lg p-5">
                    <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-3">✍️ Aceite da proposta</p>
                    <p className="text-[10px] text-slate-500 mb-6 leading-relaxed">
                      Declaro que li e aceito os termos desta proposta, autorizando o início dos trabalhos conforme
                      condições de pagamento e escopo descritos. Este aceite tem valor de contrato entre as partes.
                    </p>
                    <div className="grid grid-cols-2 gap-8 mt-8">
                      <div className="text-center">
                        <div className="border-t border-slate-400 pt-1">
                          <p className="text-[10px] font-bold text-slate-600">{cliente.nome || 'CLIENTE'}</p>
                          <p className="text-[9px] text-slate-400">{cliente.cnpj || 'CNPJ/CPF'} · Data: ____/____/______</p>
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="border-t border-slate-400 pt-1">
                          <p className="text-[10px] font-bold text-slate-600">CONTRATADA</p>
                          <p className="text-[9px] text-slate-400">Responsável técnico-comercial</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Ações */}
              <div className="flex justify-between items-center">
                <button onClick={() => setPasso(3)} className="px-4 py-2 text-slate-500 font-bold text-sm">⬅️ Voltar</button>
                <div className="flex gap-3">
                  {!codigoSalvo && (
                    <button onClick={salvarProposta} disabled={loading}
                      className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-bold text-sm shadow transition-all disabled:opacity-40">
                      {loading ? 'Salvando...' : '💾 Salvar proposta'}
                    </button>
                  )}
                  <button onClick={gerarPDF} disabled={loading}
                    className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-sm shadow transition-all disabled:opacity-40">
                    {loading ? 'Gerando...' : '📥 Baixar PDF'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
};

export default PropostaComercial;
