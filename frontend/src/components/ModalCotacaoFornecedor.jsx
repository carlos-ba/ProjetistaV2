import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import api from '../api';

/**
 * Modal do fluxo de cotação com fornecedor (Fase 1).
 *
 * 1. Usuário escolhe um fornecedor cadastrado (ou cadastra um novo inline)
 * 2. Sistema cria a cotação no banco (código único COT-ANO-SEQ-FORN)
 * 3. Baixa a planilha Excel protegida para envio ao fornecedor
 */
const fornecedorVazio = { nome: '', cnpj: '', telefone: '', email: '', contato: '' };

const ModalCotacaoFornecedor = ({ aberto, aoFechar, itens, nomeProjeto }) => {
  const [fornecedores, setFornecedores] = useState([]);
  const [fornecedorId, setFornecedorId] = useState('');
  const [validadeDias, setValidadeDias] = useState(30);

  const [mostrarCadastro, setMostrarCadastro] = useState(false);
  const [novoFornecedor, setNovoFornecedor] = useState(fornecedorVazio);

  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState('');
  const [sucesso, setSucesso] = useState(null);   // { codigo }

  useEffect(() => {
    if (aberto) {
      setErro(''); setSucesso(null);
      carregarFornecedores();
    }
  }, [aberto]);

  const carregarFornecedores = async () => {
    try {
      const r = await api.get('/api/v1/cotacoes/fornecedores');
      setFornecedores(r.data);
      if (r.data.length === 0) setMostrarCadastro(true);
    } catch {
      setErro('Erro ao carregar fornecedores.');
    }
  };

  const cadastrarFornecedor = async () => {
    if (!novoFornecedor.nome.trim()) {
      setErro('Informe ao menos o nome do fornecedor.');
      return;
    }
    setLoading(true); setErro('');
    try {
      const r = await api.post('/api/v1/cotacoes/fornecedores', novoFornecedor);
      setFornecedores(prev => [...prev, r.data]);
      setFornecedorId(String(r.data.id));
      setNovoFornecedor(fornecedorVazio);
      setMostrarCadastro(false);
    } catch {
      setErro('Erro ao cadastrar fornecedor.');
    } finally {
      setLoading(false);
    }
  };

  const gerarCotacao = async () => {
    if (!fornecedorId) {
      setErro('Selecione um fornecedor.');
      return;
    }
    setLoading(true); setErro('');
    try {
      // 1. Cria a cotação (persiste itens + gera código)
      const cot = await api.post('/api/v1/cotacoes', {
        fornecedor_id: parseInt(fornecedorId),
        nome_projeto: nomeProjeto || 'Câmara Frigorífica',
        validade_dias: parseInt(validadeDias) || 30,
        itens,
      });

      // 2. Baixa o Excel
      const resp = await api.get(`/api/v1/cotacoes/${cot.data.id}/excel`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${cot.data.codigo}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setSucesso({ codigo: cot.data.codigo });
    } catch {
      setErro('Erro ao gerar a cotação.');
    } finally {
      setLoading(false);
    }
  };

  if (!aberto) return null;

  // Portal no body — evita que ancestrais com transform quebrem o position:fixed
  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">

        {/* Header */}
        <div className="bg-amber-500 px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h3 className="text-white font-bold flex items-center gap-2">📊 Cotação com Fornecedor</h3>
          <button onClick={aoFechar} className="text-white/70 hover:text-white text-xl leading-none">✕</button>
        </div>

        <div className="p-6 space-y-5">

          {/* Sucesso */}
          {sucesso ? (
            <div className="text-center space-y-4 py-4">
              <div className="text-5xl">✅</div>
              <p className="font-bold text-emerald-700 text-lg">Cotação gerada!</p>
              <p className="text-sm text-slate-600">
                Código: <span className="font-mono font-bold text-slate-900">{sucesso.codigo}</span>
              </p>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                A planilha foi baixada. Envie ao fornecedor por e-mail ou WhatsApp.
                Quando ele devolver preenchida, importe-a na plataforma (em breve — Fase 2).
              </p>
              <button onClick={aoFechar}
                className="px-6 py-2 bg-slate-800 text-white rounded-xl font-bold text-sm hover:bg-slate-700 transition-all">
                Fechar
              </button>
            </div>
          ) : (
            <>
              {/* Resumo dos itens */}
              <div className="bg-slate-50 rounded-xl px-4 py-3 border border-slate-200">
                <p className="text-sm text-slate-600">
                  <span className="font-black text-slate-800">{itens.length}</span> itens serão incluídos na planilha de cotação
                </p>
              </div>

              {/* Seleção de fornecedor */}
              {!mostrarCadastro && (
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Fornecedor</label>
                  <div className="flex gap-2">
                    <select value={fornecedorId} onChange={e => setFornecedorId(e.target.value)}
                      className="flex-1 px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-amber-400 outline-none">
                      <option value="">Selecione...</option>
                      {fornecedores.map(f => (
                        <option key={f.id} value={f.id}>{f.nome}{f.contato ? ` — ${f.contato}` : ''}</option>
                      ))}
                    </select>
                    <button onClick={() => setMostrarCadastro(true)}
                      className="px-3 py-2 bg-indigo-50 text-indigo-600 rounded-lg text-xs font-bold border border-indigo-200 hover:bg-indigo-100 transition-all whitespace-nowrap">
                      + Novo
                    </button>
                  </div>
                </div>
              )}

              {/* Cadastro inline de fornecedor */}
              {mostrarCadastro && (
                <div className="bg-indigo-50 rounded-xl p-4 border border-indigo-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-black text-indigo-700 uppercase">Novo Fornecedor</h4>
                    {fornecedores.length > 0 && (
                      <button onClick={() => { setMostrarCadastro(false); setErro(''); }}
                        className="text-[10px] text-slate-400 hover:text-slate-600 underline">cancelar</button>
                    )}
                  </div>
                  <input value={novoFornecedor.nome} placeholder="Nome / Razão Social *"
                    onChange={e => setNovoFornecedor(p => ({ ...p, nome: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-indigo-200 text-sm outline-none focus:ring-2 focus:ring-indigo-400" />
                  <div className="grid grid-cols-2 gap-2">
                    <input value={novoFornecedor.cnpj} placeholder="CNPJ (opcional)"
                      onChange={e => setNovoFornecedor(p => ({ ...p, cnpj: e.target.value }))}
                      className="px-3 py-2 rounded-lg border border-indigo-200 text-sm outline-none" />
                    <input value={novoFornecedor.telefone} placeholder="Telefone"
                      onChange={e => setNovoFornecedor(p => ({ ...p, telefone: e.target.value }))}
                      className="px-3 py-2 rounded-lg border border-indigo-200 text-sm outline-none" />
                    <input value={novoFornecedor.contato} placeholder="Pessoa de contato"
                      onChange={e => setNovoFornecedor(p => ({ ...p, contato: e.target.value }))}
                      className="px-3 py-2 rounded-lg border border-indigo-200 text-sm outline-none" />
                    <input value={novoFornecedor.email} placeholder="E-mail" type="email"
                      onChange={e => setNovoFornecedor(p => ({ ...p, email: e.target.value }))}
                      className="px-3 py-2 rounded-lg border border-indigo-200 text-sm outline-none" />
                  </div>
                  <button onClick={cadastrarFornecedor} disabled={loading}
                    className="w-full py-2 bg-indigo-600 text-white rounded-lg font-bold text-sm hover:bg-indigo-700 transition-all disabled:opacity-40">
                    {loading ? 'Salvando...' : 'Salvar fornecedor'}
                  </button>
                </div>
              )}

              {/* Validade */}
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Validade solicitada (dias)</label>
                <input type="number" min="1" max="365" value={validadeDias}
                  onChange={e => setValidadeDias(e.target.value)}
                  className="w-28 px-3 py-2 rounded-lg border border-slate-300 text-sm text-center outline-none" />
              </div>

              {erro && <p className="text-sm text-red-600 font-bold bg-red-50 rounded-lg px-3 py-2 border border-red-200">{erro}</p>}

              {/* Ação */}
              <button onClick={gerarCotacao} disabled={loading || !fornecedorId}
                className="w-full py-3 bg-amber-500 hover:bg-amber-600 text-white rounded-xl font-bold text-sm shadow transition-all disabled:opacity-40 flex items-center justify-center gap-2">
                {loading ? 'Gerando...' : '📥 GERAR E BAIXAR PLANILHA'}
              </button>
              <p className="text-[10px] text-slate-400 text-center">
                A cotação fica registrada com código único — necessário para importar a resposta do fornecedor.
              </p>
            </>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
};

export default ModalCotacaoFornecedor;
