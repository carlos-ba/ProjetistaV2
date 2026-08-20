import { useState, useEffect } from 'react';
import api from '../api';

/**
 * Lista de preços de uma empresa (Fase B) — componente compartilhado entre dois
 * contextos: autoadministração (admin_empresa mexe na própria lista, apiBase =
 * /api/v1/produto-empresa) e implantação (superadmin mexe na lista de qualquer
 * empresa, apiBase = /api/v1/admin/empresas/{id}/produtos). O backend resolve o
 * escopo/permissão em cada caso — este componente só fala com o apiBase recebido.
 */
const produtoVazio = { descricao: '', codigo_interno: '', unidade: 'un', preco: '' };

export default function CatalogoPrecosEmpresa({ apiBase }) {
  const [produtos, setProdutos] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [novo, setNovo] = useState(null);
  const [editando, setEditando] = useState(null); // { id, ...campos }

  const carregar = async () => {
    setCarregando(true); setErro('');
    try {
      const { data } = await api.get(apiBase);
      setProdutos(data);
    } catch {
      setErro('Erro ao carregar lista de preços.');
    } finally { setCarregando(false); }
  };

  useEffect(() => { carregar(); }, [apiBase]);

  const msgErro = (e, padrao) => {
    const d = e.response?.data?.detail;
    if (typeof d === 'string') return d;
    if (d && typeof d === 'object') return Object.values(d).flat().join(' · ');
    return padrao;
  };

  const criar = async () => {
    if (!novo.descricao.trim() || !novo.preco) {
      setErro('Preencha descrição e preço.'); return;
    }
    setSalvando(true); setErro('');
    try {
      await api.post(apiBase, { ...novo, preco: parseFloat(novo.preco) });
      setNovo(null);
      await carregar();
    } catch (e) { setErro(msgErro(e, 'Erro ao criar produto.')); }
    finally { setSalvando(false); }
  };

  const salvarEdicao = async () => {
    if (!editando.descricao.trim() || !editando.preco) {
      setErro('Preencha descrição e preço.'); return;
    }
    setSalvando(true); setErro('');
    try {
      const { id, ...dados } = editando;
      await api.patch(`${apiBase}/${id}`, { ...dados, preco: parseFloat(dados.preco) });
      setEditando(null);
      await carregar();
    } catch (e) { setErro(msgErro(e, 'Erro ao salvar produto.')); }
    finally { setSalvando(false); }
  };

  const remover = async (id) => {
    if (!window.confirm('Remover este item da lista de preços?')) return;
    setErro('');
    try {
      await api.delete(`${apiBase}/${id}`);
      await carregar();
    } catch (e) { setErro(msgErro(e, 'Erro ao remover produto.')); }
  };

  const toggleAtivo = async (produto) => {
    setErro('');
    try {
      await api.patch(`${apiBase}/${produto.id}`, { ativo: !produto.ativo });
      await carregar();
    } catch (e) { setErro(msgErro(e, 'Erro ao atualizar produto.')); }
  };

  const campo = "w-full px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs outline-none focus:ring-2 focus:ring-indigo-400";

  return (
    <div className="space-y-2">
      {erro && <p className="text-[11px] text-red-500">{erro}</p>}

      {carregando ? (
        <p className="text-xs text-slate-400 py-3 text-center">Carregando…</p>
      ) : produtos.length === 0 && !novo ? (
        <p className="text-xs text-slate-400 italic py-1">Nenhum item cadastrado ainda.</p>
      ) : (
        <div className="space-y-1.5">
          {produtos.map(p => (
            editando?.id === p.id ? (
              <div key={p.id} className="bg-white rounded-lg border-2 border-indigo-200 p-2.5 space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <input className={campo} placeholder="Descrição" value={editando.descricao}
                    onChange={e => setEditando(v => ({ ...v, descricao: e.target.value }))} />
                  <input className={campo} placeholder="Código interno" value={editando.codigo_interno || ''}
                    onChange={e => setEditando(v => ({ ...v, codigo_interno: e.target.value }))} />
                  <input className={campo} placeholder="Unidade" value={editando.unidade}
                    onChange={e => setEditando(v => ({ ...v, unidade: e.target.value }))} />
                  <input className={campo} placeholder="Preço" type="number" step="0.01" value={editando.preco}
                    onChange={e => setEditando(v => ({ ...v, preco: e.target.value }))} />
                </div>
                <div className="flex gap-2 justify-end">
                  <button onClick={() => { setEditando(null); setErro(''); }}
                    className="text-[11px] px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50">Cancelar</button>
                  <button onClick={salvarEdicao} disabled={salvando}
                    className="text-[11px] px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-bold hover:bg-indigo-700 disabled:opacity-50">
                    {salvando ? 'Salvando...' : 'Salvar'}
                  </button>
                </div>
              </div>
            ) : (
              <div key={p.id} className={`flex items-center justify-between rounded-lg px-3 py-2 border ${
                p.ativo ? 'bg-white border-slate-100' : 'bg-slate-100/70 border-slate-200'}`}>
                <div className="min-w-0">
                  <p className={`text-sm font-semibold truncate ${p.ativo ? 'text-slate-800' : 'text-slate-400 line-through'}`}>
                    {p.descricao}
                  </p>
                  <p className="text-[10px] text-slate-400">
                    {p.codigo_interno ? `${p.codigo_interno} · ` : ''}
                    R$ {p.preco.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} / {p.unidade}
                  </p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button onClick={() => { setEditando({ ...p, codigo_interno: p.codigo_interno || '' }); setErro(''); }}
                    className="text-[10px] px-2 py-1 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50">Editar</button>
                  <button onClick={() => toggleAtivo(p)}
                    className={`text-[10px] px-2 py-1 rounded-lg border ${p.ativo
                      ? 'text-slate-400 hover:text-amber-600 hover:bg-amber-50 border-transparent hover:border-amber-200'
                      : 'bg-emerald-50 text-emerald-700 font-bold border-emerald-200 hover:bg-emerald-100'}`}>
                    {p.ativo ? 'Desativar' : 'Reativar'}
                  </button>
                  <button onClick={() => remover(p.id)}
                    className="text-[10px] px-2 py-1 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 border border-transparent hover:border-red-200">
                    Remover
                  </button>
                </div>
              </div>
            )
          ))}
        </div>
      )}

      {novo ? (
        <div className="bg-white rounded-lg border-2 border-indigo-200 p-2.5 space-y-2 mt-2">
          <div className="grid grid-cols-2 gap-2">
            <input className={campo} placeholder="Descrição *" value={novo.descricao}
              onChange={e => setNovo(v => ({ ...v, descricao: e.target.value }))} />
            <input className={campo} placeholder="Código interno" value={novo.codigo_interno}
              onChange={e => setNovo(v => ({ ...v, codigo_interno: e.target.value }))} />
            <input className={campo} placeholder="Unidade" value={novo.unidade}
              onChange={e => setNovo(v => ({ ...v, unidade: e.target.value }))} />
            <input className={campo} placeholder="Preço *" type="number" step="0.01" value={novo.preco}
              onChange={e => setNovo(v => ({ ...v, preco: e.target.value }))} />
          </div>
          <p className="text-[10px] text-slate-400">
            A descrição precisa bater com o nome do item no dimensionamento pra o preço entrar
            automaticamente no orçamento — sem cotação nem digitação toda vez.
          </p>
          <div className="flex gap-2 justify-end">
            <button onClick={() => { setNovo(null); setErro(''); }}
              className="text-[11px] px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50">Cancelar</button>
            <button onClick={criar} disabled={salvando}
              className="text-[11px] px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-bold hover:bg-indigo-700 disabled:opacity-50">
              {salvando ? 'Criando...' : 'Adicionar'}
            </button>
          </div>
        </div>
      ) : (
        <button onClick={() => { setNovo({ ...produtoVazio }); setErro(''); }}
          className="text-xs font-bold text-indigo-600 hover:underline mt-1">
          + Adicionar item
        </button>
      )}
    </div>
  );
}
