import React, { useState, useEffect, useRef } from 'react';
import api from '../api';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import ModalCotacaoFornecedor from './ModalCotacaoFornecedor';

const agruparItens = (itens) => {
  const cats = {
    "Painéis e Isolamento": [],
    "Equipamentos Principais": [],
    "Tubulação e Conexões": [],
    "Componentes de Fluxo": [],
    "Outros": [],
  };
  itens.forEach(l => {
    const n = (l.item || '').toLowerCase();
    if (n.includes('painel') || n.includes('isolamento') || n.includes('piso') || n.includes('placa'))
      cats["Painéis e Isolamento"].push(l);
    else if (n.includes('condensadora') || n.includes('evaporador') || n.includes('compressor') || n.includes('(eq)'))
      cats["Equipamentos Principais"].push(l);
    else if (n.includes('tubo') || n.includes('solda') || n.includes('armacel'))
      cats["Tubulação e Conexões"].push(l);
    else if (n.includes('válvula') || n.includes('filtro') || n.includes('separador') || n.includes('visor') || n.includes('pressostato'))
      cats["Componentes de Fluxo"].push(l);
    else cats["Outros"].push(l);
  });
  return cats;
};

// ── Linha de complemento em branco ───────────────────────────────────────
const novoComplemento = () => ({ descricao: '', qtde: 1, unidade: 'un', preco_unit: '' });

const GeradorOrcamento = ({ dadosAutomaticos, aoRemoverEquipamento, aoReiniciar }) => {
  const propostaRef = useRef(null);

  // ── Checkboxes para aprovar/desmarcar itens ───────────────────────────
  const [materiaisAtivos,     setMateriaisAtivos]     = useState({});
  const [equipamentosAtivos,  setEquipamentosAtivos]  = useState({});
  const [listaAprovada,       setListaAprovada]       = useState(false);

  // ── Complementos livres (sem catálogo) ───────────────────────────────
  const [complementos, setComplementos] = useState([novoComplemento()]);

  // ── Orçamento e UI ───────────────────────────────────────────────────
  const [orcamento,    setOrcamento]    = useState(null);
  const [erro,         setErro]         = useState(null);
  const [loading,      setLoading]      = useState(false);
  const [dadosCliente, setDadosCliente] = useState({ nome: '', cnpj: '', contato: '', celular: '', email: '' });

  // Reinicia checkboxes quando dadosAutomaticos muda
  useEffect(() => {
    const m = {}; (dadosAutomaticos?.materiais    || []).forEach((_, i) => { m[i] = true; }); setMateriaisAtivos(m);
    const e = {}; (dadosAutomaticos?.equipamentos || []).forEach((_, i) => { e[i] = true; }); setEquipamentosAtivos(e);
    setListaAprovada(false);
    setOrcamento(null);
  }, [dadosAutomaticos]);

  const toggleMaterial    = (i) => setMateriaisAtivos(p => ({ ...p, [i]: !p[i] }));
  const toggleEquipamento = (i) => setEquipamentosAtivos(p => ({ ...p, [i]: !p[i] }));

  const materiaisAprovados    = (dadosAutomaticos?.materiais    || []).filter((_, i) => materiaisAtivos[i]);
  const equipamentosAprovados = (dadosAutomaticos?.equipamentos || []).filter((_, i) => equipamentosAtivos[i]);
  const totalItens = materiaisAprovados.length + equipamentosAprovados.length;

  // ── Complementos ─────────────────────────────────────────────────────
  const updateComplemento = (i, f, v) => {
    const l = [...complementos]; l[i] = { ...l[i], [f]: v }; setComplementos(l);
  };
  const removerComplemento = (i) => setComplementos(complementos.filter((_, j) => j !== i));
  const complementosPreenchidos = complementos.filter(c => c.descricao.trim());

  // ── Dados do cliente ─────────────────────────────────────────────────
  const handleClienteChange = (e) => setDadosCliente(p => ({ ...p, [e.target.name]: e.target.value }));

  // ── Gerar orçamento ───────────────────────────────────────────────────
  const gerarOrcamento = async () => {
    setLoading(true); setErro(null);
    try {
      const payload = {
        materiais: materiaisAprovados.map(m => ({
          id: m.id,
          // Inclui dimensão no nome do item quando disponível
          item: m.comprimento ? `${m.item} ${m.comprimento}m` : m.item,
          qtde: m.quantidade || m.qtd || 1,
          detalhe: [m.detalhe || m.descricao, m.area_total ? `${m.area_total} m²` : null].filter(Boolean).join(' — '),
        })),
        equipamentos: equipamentosAprovados.map(e => ({
          id: e.id, item: e.nome,
          qtde: e.qtde || 1,
          detalhe: e.detalhe || '',
        })),
      };
      const r = await api.post('/api/v1/orcamento', payload);
      setOrcamento(r.data);
    } catch { setErro("Erro ao gerar orçamento."); }
    finally { setLoading(false); }
  };

  // ── Total dos complementos ────────────────────────────────────────────
  const totalComplementos = complementosPreenchidos.reduce((s, c) => {
    const p = parseFloat(c.preco_unit) || 0;
    const q = parseFloat(c.qtde) || 1;
    return s + p * q;
  }, 0);

  const totalGeral = (orcamento?.['custo_total_projeto_R$'] || 0) + totalComplementos;

  // ── PDF ───────────────────────────────────────────────────────────────
  const gerarPDF = async () => {
    if (!propostaRef.current) return;
    setLoading(true);
    try {
      const canvas = await html2canvas(propostaRef.current, { scale: 2, useCORS: true, logging: false });
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pw = pdf.internal.pageSize.getWidth();
      const ph = pdf.internal.pageSize.getHeight();
      const ch = (canvas.height * pw) / canvas.width;
      let left = ch, pos = 0;
      pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, pos, pw, ch);
      left -= ph;
      while (left >= 0) { pos = left - ch; pdf.addPage(); pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, pos, pw, ch); left -= ph; }
      pdf.save(`Orcamento_${dadosCliente.nome?.replace(/\s+/g, '_') || 'Camara'}.pdf`);
    } catch { setErro("Erro ao gerar PDF."); }
    finally { setLoading(false); }
  };

  // ── Cotação com fornecedor (Fase 1) ───────────────────────────────────
  const [modalCotacaoAberto, setModalCotacaoAberto] = useState(false);

  const montarItensCotacao = () => [
    ...equipamentosAprovados.map(e => ({
      tipo_item: e.categoria || 'Equipamento',   // ex: "Unidade Condensadora", "Evaporadora"
      ref_id:    e.id || null,
      descricao: e.nome || e.item,
      detalhe:   e.detalhe || '',
      qtde:      e.qtde || 1,
      unidade:   'un',
    })),
    ...materiaisAprovados.map(m => {
      // Extrai número do campo quantidade — pode vir como int, float ou string "24.50 m²"
      const rawQtd = m.quantidade ?? m.qtd;
      const qtdNum = parseFloat(String(rawQtd));
      const qtd    = isNaN(qtdNum) ? 1 : qtdNum;

      // Para materiais_extras do gabinete (qtd é string), inclui o texto original no detalhe
      const detalheQtd = (typeof rawQtd === 'string' && isNaN(parseFloat(rawQtd)))
        ? rawQtd : null;

      return {
        tipo_item: m.item?.toLowerCase().includes('válvula') || m.item?.toLowerCase().includes('separador')
                     ? 'Componente' : 'Material',
        ref_id:    m.id || null,
        descricao: m.comprimento ? `${m.item} ${m.comprimento}m` : m.item,
        detalhe:   [m.detalhe || m.descricao, m.area_total ? `${m.area_total} m²` : detalheQtd].filter(Boolean).join(' — '),
        qtde:      qtd,
        unidade:   m.unidade || 'un',
      };
    }),
    ...complementosPreenchidos.map(c => ({
      tipo_item: 'Complemento',
      ref_id:    null,
      descricao: c.descricao,
      detalhe:   '',
      qtde:      parseFloat(c.qtde) || 1,
      unidade:   c.unidade || 'un',
    })),
  ];

  const enviarWhatsApp = () => {
    const msg = encodeURIComponent(`Olá ${dadosCliente.contato || dadosCliente.nome || 'Cliente'}!\n\nOrçamento câmara frigorífica:\n*Total: R$ ${totalGeral.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}*\n\nEnvio o PDF em anexo.`);
    const tel = (dadosCliente.celular || '').replace(/\D/g, '');
    window.open(tel ? `https://api.whatsapp.com/send?phone=55${tel}&text=${msg}` : `https://api.whatsapp.com/send?text=${msg}`, '_blank');
  };

  return (
    <div className="space-y-6 pb-12 print:p-0 print:space-y-4">

      {/* ══ 1. LISTA COM CHECKBOXES ══ */}
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 shadow-sm print:hidden">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-amber-900 font-bold flex items-center gap-2">
            📋 Itens do Dimensionamento — Selecione o que incluir
          </h3>
          <button onClick={() => { if (window.confirm("Limpar todo o dimensionamento?")) aoReiniciar(); }}
            className="px-3 py-1.5 bg-amber-100 hover:bg-amber-200 text-amber-700 rounded-lg text-xs font-bold border border-amber-200 transition-all">
            🗑️ LIMPAR TUDO
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Materiais */}
          <div>
            <h4 className="text-xs font-black text-amber-700 uppercase mb-3 tracking-widest">Materiais e Componentes</h4>
            {(dadosAutomaticos?.materiais || []).length === 0
              ? <p className="text-amber-600/50 italic text-sm">Nenhum material calculado.</p>
              : (dadosAutomaticos.materiais.map((item, i) => (
                <label key={i} className={`flex items-start gap-3 p-3 rounded-xl border mb-2 cursor-pointer transition-all ${materiaisAtivos[i] ? 'bg-white border-amber-200 shadow-sm' : 'bg-amber-50/30 border-amber-100 opacity-50'}`}>
                  <input type="checkbox" checked={!!materiaisAtivos[i]} onChange={() => toggleMaterial(i)} className="mt-0.5 w-4 h-4 accent-amber-600 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-bold leading-tight ${materiaisAtivos[i] ? 'text-slate-800' : 'text-slate-400 line-through'}`}>
                      {item.item}
                      {item.comprimento && (
                        <span className="font-normal text-slate-500 ml-1 text-xs">— {item.comprimento}m</span>
                      )}
                    </p>
                    <p className="text-[10px] text-slate-500 mt-0.5 truncate">{item.descricao || item.detalhe}</p>
                  </div>
                  <div className="text-right flex-shrink-0 ml-2">
                    <span className="text-amber-700 font-black text-xs block">
                      {item.quantidade ? `${item.quantidade} un` : item.qtd}
                    </span>
                    {item.area_total && (
                      <span className="text-[10px] text-slate-400">({item.area_total} m²)</span>
                    )}
                  </div>
                </label>
              )))}
          </div>

          {/* Equipamentos */}
          <div>
            <h4 className="text-xs font-black text-amber-700 uppercase mb-3 tracking-widest">Equipamentos</h4>
            {(dadosAutomaticos?.equipamentos || []).length === 0
              ? <p className="text-amber-600/50 italic text-sm">Nenhum equipamento selecionado.</p>
              : (dadosAutomaticos.equipamentos.map((eq, i) => (
                <label key={i} className={`flex items-start gap-3 p-3 rounded-xl border mb-2 cursor-pointer transition-all ${equipamentosAtivos[i] ? 'bg-white border-emerald-200 shadow-sm' : 'bg-amber-50/30 border-amber-100 opacity-50'}`}>
                  <input type="checkbox" checked={!!equipamentosAtivos[i]} onChange={() => toggleEquipamento(i)} className="mt-0.5 w-4 h-4 accent-emerald-600 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-bold leading-tight ${equipamentosAtivos[i] ? 'text-emerald-800' : 'text-slate-400 line-through'}`}>
                      {eq.qtde > 1 ? `${eq.qtde}× ` : ''}{eq.nome}
                    </p>
                    <p className="text-[10px] text-slate-500 mt-0.5">{eq.detalhe}</p>
                  </div>
                  <button onClick={e => { e.preventDefault(); aoRemoverEquipamento(i); }}
                    className="w-6 h-6 flex-shrink-0 flex items-center justify-center rounded-full bg-red-50 text-red-400 hover:bg-red-500 hover:text-white transition-all text-xs" title="Remover">✕</button>
                </label>
              )))}
          </div>
        </div>

        {/* Rodapé com botão APROVAR */}
        <div className={`mt-6 pt-5 border-t border-amber-200 flex flex-col sm:flex-row items-center justify-between gap-4 ${listaAprovada ? 'bg-emerald-50 -mx-6 -mb-6 px-6 pb-6 rounded-b-2xl' : ''}`}>
          <p className="text-sm text-amber-700 font-medium">
            <span className="font-black">{materiaisAprovados.length}</span> materiais +{' '}
            <span className="font-black">{equipamentosAprovados.length}</span> equipamentos selecionados
            {totalItens === 0 && <span className="text-red-500 ml-2">— selecione ao menos 1 item</span>}
          </p>
          {!listaAprovada ? (
            <button onClick={() => totalItens > 0 && setListaAprovada(true)} disabled={totalItens === 0}
              className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-sm shadow transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2">
              ✅ APROVAR LISTA E GERAR ORÇAMENTO
            </button>
          ) : (
            <div className="flex items-center gap-3">
              <span className="text-emerald-700 font-bold text-sm">✅ Lista aprovada — {totalItens} itens</span>
              <button onClick={() => setListaAprovada(false)} className="text-xs text-slate-500 hover:text-slate-700 underline">Revisar</button>
            </div>
          )}
        </div>
      </div>

      {/* ══ 2. CARRINHO (só após aprovar) ══ */}
      {listaAprovada && (
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden print:hidden animate-in fade-in duration-500">
          <div className="bg-slate-800 px-6 py-4 text-white flex justify-between items-center">
            <h3 className="font-bold flex items-center gap-2">🛒 Carrinho de Compras</h3>
            <div className="flex items-center gap-3">
              <span className="text-[10px] bg-white/20 px-2 py-1 rounded uppercase font-bold tracking-widest">
                {totalItens} itens aprovados
              </span>
              <button
                onClick={() => { setListaAprovada(false); setOrcamento(null); }}
                className="text-[10px] font-bold text-slate-400 hover:text-white border border-slate-600 hover:border-slate-400 px-2 py-1 rounded transition-all"
                title="Voltar para a lista e alterar seleção"
              >
                ← Revisar lista
              </button>
            </div>
          </div>

          <div className="p-6 space-y-6">

            {/* Resumo dos itens aprovados (somente leitura) */}
            <div className="bg-slate-50 rounded-xl border border-slate-200 overflow-hidden">
              <div className="px-4 py-2 bg-slate-100 border-b border-slate-200">
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Itens do Dimensionamento</span>
              </div>
              <div className="divide-y divide-slate-100 max-h-48 overflow-y-auto">
                {equipamentosAprovados.map((e, i) => (
                  <div key={`eq-${i}`} className="flex items-center justify-between px-4 py-2">
                    <span className="text-sm text-emerald-700 font-semibold truncate">{e.qtde > 1 ? `${e.qtde}× ` : ''}{e.nome}</span>
                    <span className="text-[10px] text-slate-400 ml-2 flex-shrink-0">equipamento</span>
                  </div>
                ))}
                {materiaisAprovados.map((m, i) => (
                  <div key={`mat-${i}`} className="px-4 py-2 border-b border-slate-50 last:border-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <span className="text-sm text-slate-700 font-medium">
                          {m.item}
                          {m.comprimento && <span className="text-slate-400 ml-1 text-xs">— {m.comprimento}m</span>}
                        </span>
                        {/* Especificação do painel: nucleo, espessura, largura, fabricante */}
                        {(m.detalhe || m.descricao) && (
                          <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                            {m.detalhe || m.descricao}
                          </p>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400 flex-shrink-0 text-right">
                        <span className="block">{m.quantidade ? `${m.quantidade} un` : m.qtd}</span>
                        {m.area_total && <span className="block">({m.area_total} m²)</span>}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Complementos livres */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-bold text-slate-700 uppercase tracking-tight flex items-center gap-2">
                  ➕ Complementos
                  <span className="text-[10px] font-normal text-slate-400 normal-case">
                    — fluido de limpeza, material elétrico, etc.
                  </span>
                </h4>
              </div>

              <div className="space-y-2">
                {complementos.map((c, i) => (
                  <div key={i} className="grid grid-cols-12 gap-2 items-center">
                    <input
                      value={c.descricao} onChange={e => updateComplemento(i, 'descricao', e.target.value)}
                      placeholder="Descrição do item..."
                      className="col-span-5 px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-400 outline-none"
                    />
                    <input
                      type="number" min="1" value={c.qtde} onChange={e => updateComplemento(i, 'qtde', e.target.value)}
                      className="col-span-1 px-2 py-2 rounded-lg border border-slate-300 text-sm text-center outline-none"
                    />
                    <input
                      value={c.unidade} onChange={e => updateComplemento(i, 'unidade', e.target.value)}
                      placeholder="un"
                      className="col-span-2 px-2 py-2 rounded-lg border border-slate-300 text-sm text-center outline-none"
                    />
                    <div className="col-span-3 relative">
                      <span className="absolute left-3 top-2 text-slate-400 text-sm">R$</span>
                      <input
                        type="number" min="0" step="0.01" value={c.preco_unit} onChange={e => updateComplemento(i, 'preco_unit', e.target.value)}
                        placeholder="0,00"
                        className="w-full pl-8 pr-2 py-2 rounded-lg border border-slate-300 text-sm outline-none"
                      />
                    </div>
                    <button onClick={() => complementos.length > 1 ? removerComplemento(i) : updateComplemento(i, 'descricao', '')}
                      className="col-span-1 text-slate-300 hover:text-red-400 transition-colors text-center">✕</button>
                  </div>
                ))}
              </div>

              <p className="text-[10px] text-slate-400 mt-2 mb-3">
                💡 Deixe o valor em branco para itens "a cotação"
              </p>

              <button onClick={() => setComplementos([...complementos, novoComplemento()])}
                className="text-xs font-bold text-indigo-600 hover:underline flex items-center gap-1">
                + Adicionar complemento
              </button>
            </div>

            {/* Dados do Cliente */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <h4 className="text-sm font-bold text-slate-700 uppercase tracking-tight border-b pb-2 mb-4 flex items-center gap-2">
                👤 Dados do Cliente
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { name: 'nome',    label: 'Nome / Razão Social', ph: 'Frigorífico Silva LTDA',  span: 1 },
                  { name: 'cnpj',    label: 'CNPJ / CPF',          ph: '00.000.000/0001-00',       span: 1 },
                  { name: 'contato', label: 'Pessoa de Contato',   ph: 'João Silva',               span: 1 },
                  { name: 'celular', label: 'Celular / WhatsApp',  ph: '(00) 00000-0000',          span: 1 },
                  { name: 'email',   label: 'E-mail',              ph: 'cliente@email.com',         span: 2 },
                ].map(f => (
                  <div key={f.name} className={`space-y-1 ${f.span === 2 ? 'md:col-span-2' : ''}`}>
                    <label className="text-[10px] font-bold text-slate-500 uppercase">{f.label}</label>
                    <input name={f.name} value={dadosCliente[f.name]} onChange={handleClienteChange}
                      placeholder={f.ph} type={f.name === 'email' ? 'email' : 'text'}
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none" />
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="p-6 bg-slate-50 border-t border-slate-100">
            {/* Duas opções para o técnico */}
            <p className="text-center text-xs text-slate-400 mb-4 font-medium uppercase tracking-widest">
              O que deseja fazer com esta lista?
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">

              {/* Opção A: Enviar para cotação */}
              <button onClick={() => setModalCotacaoAberto(true)} disabled={loading}
                className="w-full sm:w-auto px-6 py-3 bg-amber-500 hover:bg-amber-600 text-white rounded-xl font-bold text-sm shadow transition-all disabled:opacity-40 flex items-center justify-center gap-2">
                📊 GERAR PLANILHA DE COTAÇÃO
                <span className="text-[10px] font-normal opacity-80">— enviar ao fornecedor</span>
              </button>

              <span className="text-slate-300 font-bold hidden sm:block">ou</span>

              {/* Opção B: Já tem preços, gera orçamento */}
              <button onClick={gerarOrcamento} disabled={loading}
                className="w-full sm:w-auto px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-sm shadow-lg hover:-translate-y-0.5 transition-all disabled:bg-slate-300 flex items-center justify-center gap-2">
                💰 GERAR PROPOSTA AO CLIENTE
                <span className="text-[10px] font-normal opacity-80">— já tenho os preços</span>
              </button>
            </div>
            {loading && <p className="text-center text-xs text-slate-400 mt-3 animate-pulse">Processando...</p>}
          </div>
        </div>
      )}

      {erro && <div className="p-4 bg-red-100 text-red-700 rounded-xl text-center font-bold border border-red-200">{erro}</div>}

      {/* Modal de cotação com fornecedor */}
      <ModalCotacaoFornecedor
        aberto={modalCotacaoAberto}
        aoFechar={() => setModalCotacaoAberto(false)}
        itens={modalCotacaoAberto ? montarItensCotacao() : []}
        nomeProjeto={dadosCliente.nome ? `Câmara Frigorífica — ${dadosCliente.nome}` : 'Câmara Frigorífica'}
      />

      {/* ══ 3. PROPOSTA FINAL ══ */}
      {orcamento && (
        <div ref={propostaRef} className="bg-white border-2 border-slate-900 rounded-2xl overflow-hidden shadow-2xl animate-in fade-in slide-in-from-bottom-8 duration-700 print:shadow-none print:border-none print:rounded-none print:m-0 print:p-0">
          <div className="bg-slate-900 text-white p-8 flex justify-between items-center print:bg-white print:text-slate-900 print:border-b-2 print:border-slate-900 print:px-0">
            <div>
              <h3 className="text-2xl font-black tracking-tighter">PROPOSTA TÉCNICA COMERCIAL</h3>
              <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mt-1 print:text-slate-500">Engenharia de Refrigeração</p>
            </div>
            <div className="text-right hidden sm:block">
              <div className="text-xs text-slate-500 font-bold">DATA</div>
              <div className="text-sm font-bold">{new Date().toLocaleDateString('pt-BR')}</div>
            </div>
          </div>

          <div className="p-8 space-y-10 print:px-0 print:py-6">
            {/* Cliente */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-50 p-6 rounded-xl border border-slate-200 relative print:bg-white print:border-slate-300">
              <button onClick={() => setOrcamento(null)}
                className="absolute top-4 right-4 bg-white border border-slate-200 p-2 rounded-lg text-xs font-bold text-slate-400 hover:text-indigo-600 hover:border-indigo-200 transition-all shadow-sm print:hidden flex items-center gap-1">
                ✏️ EDITAR
              </button>
              <div className="space-y-2">
                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Informações do Cliente</h4>
                <p className="text-lg font-black text-slate-900">{dadosCliente.nome || 'Nome não informado'}</p>
                <p className="text-sm text-slate-600 font-bold">CNPJ/CPF: {dadosCliente.cnpj || '---'}</p>
              </div>
              <div className="grid grid-cols-2 gap-4 pt-4 md:pt-0 border-t md:border-t-0 md:border-l border-slate-200 md:pl-6">
                {[['Contato', dadosCliente.contato], ['Celular', dadosCliente.celular]].map(([l, v]) => (
                  <div key={l}><p className="text-[10px] font-black text-slate-400 uppercase">{l}</p><p className="text-sm font-bold text-slate-800">{v || '---'}</p></div>
                ))}
                <div className="col-span-2"><p className="text-[10px] font-black text-slate-400 uppercase">E-mail</p><p className="text-sm font-bold text-slate-800">{dadosCliente.email || '---'}</p></div>
              </div>
            </div>

            {/* Imagem */}
            {dadosAutomaticos?.imagem_projeto && (
              <div className="border border-slate-200 rounded-xl overflow-hidden bg-slate-50 p-4">
                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">Planta Técnica do Projeto</h4>
                <img src={dadosAutomaticos.imagem_projeto} alt="Planta" className="max-h-[300px] mx-auto object-contain print:max-h-[400px]" />
              </div>
            )}

            {/* Itens do dimensionamento */}
            {Object.entries(agruparItens(orcamento.detalhamento_itens)).map(([cat, itens]) =>
              itens.length > 0 && (
                <div key={cat}>
                  <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4 border-b border-slate-100 pb-2">{cat}</h4>
                  <div className="space-y-4">
                    {itens.map((l, i) => (
                      <div key={i} className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="font-bold text-slate-800 leading-tight">{l.item}</div>
                          {l.detalhe && <div className="text-xs text-slate-400 mt-0.5">{l.detalhe}</div>}
                        </div>
                        <div className="w-24 text-center text-sm text-slate-600 font-medium">{l.quantidade} {l.unidade}</div>
                        <div className="w-32 text-right font-black text-slate-900">R$ {l['custo_total_R$']?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            )}

            {/* Complementos */}
            {complementosPreenchidos.length > 0 && (
              <div>
                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4 border-b border-slate-100 pb-2">Complementos e Materiais Adicionais</h4>
                <div className="space-y-4">
                  {complementosPreenchidos.map((c, i) => (
                    <div key={i} className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="font-bold text-slate-800 leading-tight">{c.descricao}</div>
                      </div>
                      <div className="w-24 text-center text-sm text-slate-600 font-medium">{c.qtde} {c.unidade}</div>
                      <div className="w-32 text-right font-black text-slate-900">
                        {c.preco_unit
                          ? `R$ ${(parseFloat(c.preco_unit) * parseFloat(c.qtde)).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                          : <span className="text-slate-400 font-normal italic text-sm">A cotação</span>
                        }
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Total */}
            <div className="pt-8 border-t-4 border-slate-900 flex flex-col md:flex-row justify-between items-center gap-6">
              <p className="text-slate-400 text-xs max-w-xs leading-relaxed print:text-[8px]">
                * Orçamento válido por 7 dias úteis. Preços baseados em impostos vigentes. Instalação não inclusa salvo menção expressa.
                {complementosPreenchidos.some(c => !c.preco_unit) && ' Itens "a cotação" não incluídos no total.'}
              </p>
              <div className="text-right">
                <div className="text-slate-500 text-sm font-bold uppercase">Investimento Total</div>
                <div className="text-4xl font-black text-indigo-600">
                  R$ {totalGeral.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </div>
              </div>
            </div>
          </div>

          {/* Ações */}
          <div className="bg-slate-50 p-6 border-t border-slate-100 flex justify-center gap-4 print:hidden">
            <button onClick={() => window.print()} className="px-6 py-2 bg-slate-200 text-slate-700 rounded-lg font-bold hover:bg-slate-300 transition-all">Imprimir 🖨️</button>
            <button onClick={gerarPDF} disabled={loading} className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-bold hover:bg-indigo-700 transition-all disabled:bg-slate-300">
              {loading ? 'Gerando...' : 'Baixar PDF 📥'}
            </button>
            <button onClick={enviarWhatsApp} className="px-6 py-2 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 transition-all">WhatsApp 💬</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default GeradorOrcamento;
