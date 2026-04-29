import React, { useState, useEffect, useRef } from 'react';
import api from '../api';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

const GeradorOrcamento = ({ dadosAutomaticos, aoRemoverEquipamento, aoReiniciar }) => {
  const propostaRef = useRef(null);
  const [listaMateriais, setListaMateriais] = useState([]);
  const [listaEquipamentos, setListaEquipamentos] = useState([]);
  const [selecaoMateriais, setSelecaoMateriais] = useState([{ id: '', qtde: 1 }]);
  const [selecaoEquipamentos, setSelecaoEquipamentos] = useState([{ id: '', qtde: 1 }]);
  const [orcamento, setOrcamento] = useState(null);
  const [erro, setErro] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dadosCliente, setDadosCliente] = useState({
    nome: '',
    cnpj: '',
    contato: '',
    celular: '',
    email: ''
  });

  const handleClienteChange = (e) => {
    const { name, value } = e.target;
    setDadosCliente(prev => ({ ...prev, [name]: value }));
  };

  useEffect(() => {
    const carregarCatalogos = async () => {
      try {
        const respMat = await api.get('/api/v1/materiais/');
        const respEq = await api.get('/api/v1/equipamentos/');
        setListaMateriais(Array.isArray(respMat.data) ? respMat.data : respMat.data.results || []);
        setListaEquipamentos(Array.isArray(respEq.data) ? respEq.data : respEq.data.results || []);
      } catch (err) {
        setErro("Não foi possível carregar o catálogo de produtos.");
      }
    };
    carregarCatalogos();
  }, []);

  const updateMaterial = (index, field, value) => {
    const novaLista = [...selecaoMateriais];
    novaLista[index][field] = value;
    setSelecaoMateriais(novaLista);
  };
  const addLinhaMaterial = () => setSelecaoMateriais([...selecaoMateriais, { id: '', qtde: 1 }]);
  const removerLinhaMaterial = (idx) => setSelecaoMateriais(selecaoMateriais.filter((_, i) => i !== idx));

  const updateEquipamento = (index, field, value) => {
    const novaLista = [...selecaoEquipamentos];
    novaLista[index][field] = value;
    setSelecaoEquipamentos(novaLista);
  };
  const addLinhaEquipamento = () => setSelecaoEquipamentos([...selecaoEquipamentos, { id: '', qtde: 1 }]);
  const removerLinhaEquipamento = (idx) => setSelecaoEquipamentos(selecaoEquipamentos.filter((_, i) => i !== idx));

  const gerarOrcamento = async () => {
    setLoading(true);
    try {
      setErro(null);
      
      // Mescla os itens automáticos com os manuais
      const materiaisAuto = (dadosAutomaticos?.materiais || []).map(m => ({
        id: m.id,
        item: m.item,
        qtde: m.quantidade || m.qtd || 1,
        detalhe: m.detalhe || m.descricao
      }));

      const equipamentosAuto = (dadosAutomaticos?.equipamentos || []).map(e => ({
        id: e.id,
        item: e.nome,
        qtde: e.qtde || 1,
        detalhe: e.detalhe
      }));

      const payload = {
        materiais: [
          ...materiaisAuto,
          ...selecaoMateriais.filter(m => m.id && m.qtde > 0)
        ],
        equipamentos: [
          ...equipamentosAuto,
          ...selecaoEquipamentos.filter(e => e.id && e.qtde > 0)
        ]
      };
      
      const response = await api.post('/api/v1/gerar-orcamento/', payload);
      setOrcamento(response.data);
    } catch (err) {
      setErro("Erro ao gerar orçamento.");
    } finally {
      setLoading(false);
    }
  };

  const agruparItens = (itens) => {
    const categorias = {
      "Painéis e Isolamento": [],
      "Equipamentos Principais": [],
      "Tubulação e Conexões": [],
      "Componentes de Fluxo e Acessórios": [],
      "Outros": []
    };
    itens.forEach(linha => {
      const itemNome = linha.item.toLowerCase();
      // Melhora a identificação do item para agrupamento
      if (itemNome.includes('painel') || itemNome.includes('isolamento') || itemNome.includes('piso') || itemNome.includes('placas')) categorias["Painéis e Isolamento"].push(linha);
      else if (itemNome.includes('unidade') || itemNome.includes('evaporador') || itemNome.includes('condensadora') || itemNome.includes('(eq)')) categorias["Equipamentos Principais"].push(linha);
      else if (itemNome.includes('tubo') || itemNome.includes('solda') || itemNome.includes('fita pvc')) categorias["Tubulação e Conexões"].push(linha);
      else if (itemNome.includes('válvula') || itemNome.includes('filtro') || itemNome.includes('acumulador') || itemNome.includes('separador')) categorias["Componentes de Fluxo e Acessórios"].push(linha);
      else categorias["Outros"].push(linha);
    });
    return categorias;
  };

  const enviarWhatsApp = () => {
    if (!orcamento || !dadosCliente) return;

    const saudacao = `Olá ${dadosCliente.contato || dadosCliente.nome || 'Cliente'}, tudo bem?`;
    const resumo = `Segue o orçamento para o projeto da Câmara Frigorífica:\n\n` +
      `*Investimento Total:* R$ ${orcamento.custo_total_projeto_R$.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}\n\n` +
      `Estou enviando o PDF detalhado em anexo.`;
    
    const mensagem = encodeURIComponent(`${saudacao}\n\n${resumo}`);
    const telefone = (dadosCliente.celular || '').replace(/\D/g, '');
    
    // Se tiver telefone, envia direto para o número, senão abre o seletor de contatos
    const url = telefone 
      ? `https://api.whatsapp.com/send?phone=55${telefone}&text=${mensagem}`
      : `https://api.whatsapp.com/send?text=${mensagem}`;

    window.open(url, '_blank');
  };

  const gerarPDF = async () => {
    if (!propostaRef.current) return;
    setLoading(true);
    try {
      const element = propostaRef.current;
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        logging: false,
        ignoreElements: (el) => el.classList.contains('print:hidden')
      });
      
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const imgProps = pdf.getImageProperties(imgData);
      const canvasHeightInPdf = (imgProps.height * pdfWidth) / imgProps.width;
      
      let heightLeft = canvasHeightInPdf;
      let position = 0;

      // Primeira página
      pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, canvasHeightInPdf);
      heightLeft -= pdfHeight;

      // Adiciona mais páginas se necessário
      while (heightLeft >= 0) {
        position = heightLeft - canvasHeightInPdf;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, canvasHeightInPdf);
        heightLeft -= pdfHeight;
      }

      pdf.save(`Orcamento_${dadosCliente.nome.replace(/\s+/g, '_') || 'Camara'}.pdf`);
    } catch (err) {
      console.error("Erro ao gerar PDF:", err);
      setErro("Erro ao gerar o arquivo PDF.");
    } finally {
      setLoading(false);
    }
  };

  const temMateriaisAuto = dadosAutomaticos?.materiais && dadosAutomaticos.materiais.length > 0;
  const temEquipAuto = dadosAutomaticos?.equipamentos && dadosAutomaticos.equipamentos.length > 0;

  return (
    <div className="space-y-8 pb-12 print:p-0 print:space-y-4">
      {/* Guia de Seleção Inteligente */}
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 shadow-sm print:hidden">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <span className="text-xl">📋</span>
            <h3 className="text-amber-900 font-bold">Resumo do Dimensionamento Técnico</h3>
          </div>
          
          <button 
            onClick={() => {
              if(window.confirm("Deseja realmente limpar todo o dimensionamento e recomeçar os cálculos?")) {
                aoReiniciar();
              }
            }}
            className="flex items-center gap-2 px-4 py-2 bg-amber-100 hover:bg-amber-200 text-amber-700 rounded-lg text-xs font-black transition-all border border-amber-200"
          >
            🗑️ LIMPAR TUDO
          </button>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <h4 className="text-xs font-black text-amber-700 uppercase mb-4 tracking-widest">Materiais Calculados</h4>
            {temMateriaisAuto ? (
              <div className="space-y-3">
                {dadosAutomaticos.materiais.map((item, idx) => (
                  <div key={idx} className="bg-white/60 p-3 rounded-xl border border-amber-100 flex justify-between items-center">
                    <div>
                      <div className="font-bold text-slate-800 text-sm">{item.item}</div>
                      <div className="text-[10px] text-slate-500 uppercase font-medium">{item.descricao || item.detalhe}</div>
                    </div>
                    <div className="text-amber-700 font-black text-sm whitespace-nowrap">
                        {item.quantidade ? (
                            <span>{item.quantidade} un {item.area_total ? `(${item.area_total} m²)` : ''}</span>
                        ) : (
                            <span>{item.qtd}</span>
                        )}
                    </div>
                  </div>
                ))}
              </div>
            ) : <p className="text-amber-600/50 italic text-sm">Nenhum material pendente.</p>}
          </div>

          <div>
            <h4 className="text-xs font-black text-amber-700 uppercase mb-4 tracking-widest">Equipamentos Definidos</h4>
            {temEquipAuto ? (
              <div className="space-y-3">
                {dadosAutomaticos.equipamentos.map((eq, idx) => (
                  <div key={idx} className="bg-white p-3 rounded-xl border border-emerald-200 flex justify-between items-center shadow-sm">
                    <div>
                      <div className="font-bold text-emerald-700 text-sm">
                        {eq.qtde > 1 ? `${eq.qtde}x ` : ''}{eq.nome}
                      </div>
                      <div className="text-[10px] text-slate-500 font-medium">
                        {eq.detalhe} {eq.qtde > 1 && `(Soma: ${eq.qtde * eq.capacidade_real} kcal/h)`}
                      </div>
                    </div>
                    <button 
                      onClick={() => aoRemoverEquipamento(idx)}
                      className="w-7 h-7 flex items-center justify-center rounded-full bg-red-50 text-red-500 hover:bg-red-500 hover:text-white transition-all text-xs"
                    >✕</button>
                  </div>
                ))}
              </div>
            ) : <p className="text-amber-600/50 italic text-sm">Nenhum equipamento na lista.</p>}
          </div>
        </div>
      </div>

      {/* Carrinho de Compras Manual */}
      <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden print:hidden">
        <div className="bg-slate-800 px-6 py-4 text-white flex justify-between items-center">
           <h3 className="font-bold flex items-center gap-2">🛒 Carrinho de Compras</h3>
           <span className="text-[10px] bg-white/20 px-2 py-1 rounded uppercase font-bold tracking-widest">Confirmação de Itens</span>
        </div>
        
        <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-8">
           {/* Coluna Dados do Cliente */}
           <div id="form-dados-cliente" className="lg:col-span-2 space-y-4 bg-slate-50 p-4 rounded-xl border border-slate-200 mb-4">
              <h4 className="text-sm font-bold text-slate-700 uppercase tracking-tight border-b pb-2 flex items-center gap-2">
                <span>👤</span> Dados do Cliente
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Nome / Razão Social</label>
                  <input 
                    name="nome" value={dadosCliente.nome} onChange={handleClienteChange}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                    placeholder="Ex: Frigorífico Silva LTDA"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">CNPJ / CPF</label>
                  <input 
                    name="cnpj" value={dadosCliente.cnpj} onChange={handleClienteChange}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                    placeholder="00.000.000/0001-00"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Pessoa de Contato</label>
                  <input 
                    name="contato" value={dadosCliente.contato} onChange={handleClienteChange}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                    placeholder="Ex: João Silva"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Celular / WhatsApp</label>
                  <input 
                    name="celular" value={dadosCliente.celular} onChange={handleClienteChange}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                    placeholder="(00) 00000-0000"
                  />
                </div>
                <div className="space-y-1 md:col-span-2">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">E-mail</label>
                  <input 
                    name="email" type="email" value={dadosCliente.email} onChange={handleClienteChange}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                    placeholder="cliente@email.com"
                  />
                </div>
              </div>
           </div>

           {/* Coluna Materiais */}
           <div className="space-y-4">
              <h4 className="text-sm font-bold text-slate-400 uppercase tracking-tight border-b pb-2">1. Adicionar Materiais</h4>
              {selecaoMateriais.map((item, index) => (
                <div key={index} className="flex gap-2">
                  <select 
                    value={item.id} onChange={e => updateMaterial(index, 'id', e.target.value)}
                    className="flex-1 px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                  >
                    <option value="">Produto...</option>
                    {listaMateriais.map(m => <option key={m.id} value={m.id}>{m.nome} (R$ {m.custo})</option>)}
                  </select>
                  <input 
                    type="number" value={item.qtde} onChange={e => updateMaterial(index, 'qtde', e.target.value)}
                    className="w-16 px-2 py-2 rounded-lg border border-slate-300 text-center text-sm"
                  />
                  <button onClick={()=>removerLinhaMaterial(index)} className="text-slate-300 hover:text-red-500">✕</button>
                </div>
              ))}
              <button onClick={addLinhaMaterial} className="text-xs font-bold text-indigo-600 hover:underline">+ Adicionar Item</button>
           </div>

           {/* Coluna Equipamentos */}
           <div className="space-y-4">
              <h4 className="text-sm font-bold text-slate-400 uppercase tracking-tight border-b pb-2">2. Adicionar Equipamentos</h4>
              {selecaoEquipamentos.map((item, index) => (
                <div key={index} className="flex gap-2">
                  <select 
                    value={item.id} onChange={e => updateEquipamento(index, 'id', e.target.value)}
                    className="flex-1 px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                  >
                    <option value="">Modelo...</option>
                    {listaEquipamentos.map(e => <option key={e.id} value={e.id}>{e.modelo} (R$ {e.custo})</option>)}
                  </select>
                  <input 
                    type="number" value={item.qtde} onChange={e => updateEquipamento(index, 'qtde', e.target.value)}
                    className="w-16 px-2 py-2 rounded-lg border border-slate-300 text-center text-sm"
                  />
                  <button onClick={()=>removerLinhaEquipamento(index)} className="text-slate-300 hover:text-red-500">✕</button>
                </div>
              ))}
              <button onClick={addLinhaEquipamento} className="text-xs font-bold text-indigo-600 hover:underline">+ Adicionar Equipamento</button>
           </div>
        </div>

        <div className="p-6 bg-slate-50 border-t border-slate-100 flex justify-center">
           <button 
            onClick={gerarOrcamento} disabled={loading}
            className="px-10 py-4 bg-indigo-600 text-white rounded-xl font-black text-lg shadow-lg hover:bg-indigo-700 hover:-translate-y-1 transition-all active:translate-y-0 disabled:bg-slate-300"
           >
             {loading ? 'Processando...' : '💰 GERAR PROPOSTA FINAL'}
           </button>
        </div>
      </div>

      {erro && <div className="p-4 bg-red-100 text-red-700 rounded-xl text-center font-bold border border-red-200">{erro}</div>}

      {/* Resultado da Proposta */}
      {orcamento && (
        <div ref={propostaRef} className="bg-white border-2 border-slate-900 rounded-2xl overflow-hidden shadow-2xl animate-in fade-in slide-in-from-bottom-8 duration-700 print:shadow-none print:border-none print:rounded-none print:m-0 print:p-0">
           <div className="bg-slate-900 text-white p-8 flex justify-between items-center print:bg-white print:text-slate-900 print:border-b-2 print:border-slate-900 print:px-0">
              <div>
                <h3 className="text-2xl font-black tracking-tighter">PROPOSTA TÉCNICA COMERCIAL</h3>
                <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mt-1 print:text-slate-500">Engenharia de Refrigeração</p>
              </div>
              <div className="text-right hidden sm:block">
                <div className="text-xs text-slate-500 font-bold">DATA DO DOCUMENTO</div>
                <div className="text-sm font-bold">{new Date().toLocaleDateString('pt-BR')}</div>
              </div>
           </div>

           <div className="p-8 space-y-10 print:px-0 print:py-6">
              {/* Cabeçalho com Dados do Cliente */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-50 p-6 rounded-xl border border-slate-200 relative print:bg-white print:border-slate-300">
                {/* Botão de Edição Rápida */}
                <button 
                  onClick={() => {
                    setOrcamento(null);
                    setTimeout(() => {
                      document.getElementById('form-dados-cliente')?.scrollIntoView({ behavior: 'smooth' });
                    }, 100);
                  }}
                  className="absolute top-4 right-4 bg-white border border-slate-200 p-2 rounded-lg text-xs font-bold text-slate-400 hover:text-indigo-600 hover:border-indigo-200 transition-all shadow-sm print:hidden flex items-center gap-1"
                  title="Corrigir Dados"
                >
                  <span>✏️</span> EDITAR
                </button>

                <div className="space-y-2">
                  <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Informações do Cliente</h4>
                  <div className="space-y-1">
                    <p className="text-lg font-black text-slate-900 leading-tight">{dadosCliente.nome || 'Nome não informado'}</p>
                    <p className="text-sm text-slate-600 font-bold">CNPJ/CPF: <span className="text-slate-900">{dadosCliente.cnpj || '---'}</span></p>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 md:pt-0 border-t md:border-t-0 md:border-l border-slate-200 md:pl-6">
                  <div className="space-y-1">
                    <p className="text-[10px] font-black text-slate-400 uppercase">Contato</p>
                    <p className="text-sm font-bold text-slate-800">{dadosCliente.contato || '---'}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-[10px] font-black text-slate-400 uppercase">Celular</p>
                    <p className="text-sm font-bold text-slate-800">{dadosCliente.celular || '---'}</p>
                  </div>
                  <div className="space-y-1 sm:col-span-2">
                    <p className="text-[10px] font-black text-slate-400 uppercase">E-mail</p>
                    <p className="text-sm font-bold text-slate-800">{dadosCliente.email || '---'}</p>
                  </div>
                </div>
              </div>

              {/* Imagem da Planta do Projeto */}
              {dadosAutomaticos?.imagem_projeto && (
                <div className="border border-slate-200 rounded-xl overflow-hidden bg-slate-50 p-4 print:bg-white print:border-slate-300">
                  <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">Planta Técnica do Projeto</h4>
                  <img 
                    src={dadosAutomaticos.imagem_projeto} 
                    alt="Planta da Câmara" 
                    className="max-h-[300px] mx-auto object-contain print:max-h-[400px]"
                  />
                </div>
              )}

              {Object.entries(agruparItens(orcamento.detalhamento_itens)).map(([cat, itens]) => (
                itens.length > 0 && (
                  <div key={cat}>
                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4 border-b border-slate-100 pb-2">{cat}</h4>
                    <div className="space-y-4">
                       {itens.map((linha, idx) => (
                         <div key={idx} className="flex justify-between items-start group">
                            <div className="flex-1">
                               <div className="font-bold text-slate-800 leading-tight">{linha.item}</div>
                               {linha.detalhe && <div className="text-xs text-slate-400 mt-0.5">{linha.detalhe}</div>}
                            </div>
                            <div className="w-24 text-center text-sm text-slate-600 font-medium">
                               {linha.quantidade} {linha.unidade}
                            </div>
                            <div className="w-32 text-right font-black text-slate-900">
                               R$ {linha.custo_total_R$.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                            </div>
                         </div>
                       ))}
                    </div>
                  </div>
                )
              ))}

              <div className="pt-8 border-t-4 border-slate-900 flex flex-col md:flex-row justify-between items-center gap-6">
                 <div className="text-slate-400 text-xs max-w-xs leading-relaxed print:text-[8px]">
                    * Este orçamento tem validade de 7 dias úteis. Preços baseados em impostos vigentes. Instalação não inclusa salvo menção expressa.
                 </div>
                 <div className="text-right">
                    <div className="text-slate-500 text-sm font-bold uppercase">Investimento Total</div>
                    <div className="text-4xl font-black text-indigo-600">
                       R$ {orcamento.custo_total_projeto_R$.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                    </div>
                 </div>
              </div>
           </div>

           <div className="bg-slate-50 p-6 border-t border-slate-100 flex justify-center gap-4 print:hidden">
              <button onClick={() => window.print()} className="px-6 py-2 bg-slate-200 text-slate-700 rounded-lg font-bold hover:bg-slate-300 transition-all">Imprimir 🖨️</button>
              <button 
                onClick={gerarPDF} 
                disabled={loading}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-bold hover:bg-indigo-700 transition-all flex items-center gap-2 disabled:bg-slate-300"
              >
                {loading ? 'Gerando...' : 'Baixar PDF 📥'}
              </button>
              <button onClick={enviarWhatsApp} className="px-6 py-2 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 transition-all flex items-center gap-2">WhatsApp 💬</button>
              <button className="px-6 py-2 bg-slate-900 text-white rounded-lg font-bold hover:opacity-90 transition-all">E-mail 📧</button>
           </div>
        </div>
      )}
    </div>
  );
};

export default GeradorOrcamento;
