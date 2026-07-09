import React, { useState, useEffect } from 'react';
import api from '../api';

// Painel admin para gerenciar a classificação de itens do orçamento:
// blocos (nível 1), classificações (nível 2) e o de-para tipo_item → classificação.
export default function ClassificacaoPage({ onFechar, onAtualizar }) {
  const [arvore, setArvore] = useState(null);
  const [erro, setErro] = useState('');
  const [salvando, setSalvando] = useState(false);

  const carregar = async () => {
    try {
      const r = await api.get('/api/v1/classificacoes');
      setArvore(r.data);
      if (onAtualizar) onAtualizar(r.data);
    } catch { setErro('Erro ao carregar classificações.'); }
  };

  useEffect(() => { carregar(); }, []);

  const chamar = async (fn) => {
    setSalvando(true); setErro('');
    try { await fn(); await carregar(); }
    catch { setErro('Erro ao salvar.'); }
    finally { setSalvando(false); }
  };

  const renomearBloco = (b, nome) =>
    chamar(() => api.put(`/api/v1/classificacoes/blocos/${b.id}`, { nome, ordem: b.ordem }));
  const renomearClasse = (c, nome) =>
    chamar(() => api.put(`/api/v1/classificacoes/itens-classificacao/${c.id}`, { nome, bloco_id: c.bloco_id, ordem: c.ordem }));
  const moverClasse = (c, bloco_id) =>
    chamar(() => api.put(`/api/v1/classificacoes/itens-classificacao/${c.id}`, { nome: c.nome, bloco_id, ordem: c.ordem }));
  const remapear = (tipo_item, classificacao_id) =>
    chamar(() => api.put('/api/v1/classificacoes/mapa', { tipo_item, classificacao_id }));
  const novoBloco = () =>
    chamar(() => api.post('/api/v1/classificacoes/blocos', { nome: 'Novo Bloco', ordem: 90 }));
  const novaClasse = (bloco_id) =>
    chamar(() => api.post('/api/v1/classificacoes/itens-classificacao', { nome: 'Nova Classificação', bloco_id, ordem: 90 }));

  if (!arvore) {
    return (
      <div className="fixed inset-0 z-50 flex">
        <div className="absolute inset-0 bg-black/40" onClick={onFechar} />
        <div className="relative ml-auto w-full max-w-2xl bg-white h-full shadow-2xl flex items-center justify-center">
          <p className="text-sm text-slate-400">Carregando…</p>
        </div>
      </div>
    );
  }

  const { blocos, classificacoes, mapa } = arvore;
  const blocosOrd = [...blocos].sort((a, b) => a.ordem - b.ordem);
  const classesDoBloco = (bid) => classificacoes.filter(c => c.bloco_id === bid).sort((a, b) => a.ordem - b.ordem);
  // tipo_item por classificação (invertendo o mapa)
  const itensDaClasse = (cid) => Object.entries(mapa).filter(([, v]) => v === cid).map(([t]) => t);

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="absolute inset-0 bg-black/40" onClick={onFechar} />
      <div className="relative ml-auto w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 bg-slate-800">
          <div>
            <p className="text-sm font-black text-white">Classificação de Itens do Orçamento</p>
            <p className="text-[10px] text-slate-400">Blocos, classificações e de-para de itens</p>
          </div>
          <button onClick={onFechar} className="text-slate-400 hover:text-white text-xl leading-none">✕</button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {erro && <p className="text-xs text-red-500">{erro}</p>}

          {blocosOrd.map(b => (
            <div key={b.id} className="rounded-xl border-2 border-slate-200 p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-[9px] font-black text-slate-400 uppercase">Bloco</span>
                <input
                  defaultValue={b.nome}
                  onBlur={e => e.target.value.trim() && e.target.value !== b.nome && renomearBloco(b, e.target.value.trim())}
                  className="flex-1 text-sm font-bold text-slate-800 border-b border-transparent hover:border-slate-200 focus:border-indigo-400 outline-none px-1"
                />
                <span className="text-[9px] text-slate-400">ordem {b.ordem}</span>
              </div>

              <div className="space-y-2 pl-3">
                {classesDoBloco(b.id).map(c => (
                  <div key={c.id} className="bg-slate-50 rounded-lg p-2.5">
                    <div className="flex items-center gap-2">
                      <input
                        defaultValue={c.nome}
                        onBlur={e => e.target.value.trim() && e.target.value !== c.nome && renomearClasse(c, e.target.value.trim())}
                        className="flex-1 text-xs font-semibold text-slate-700 border-b border-transparent hover:border-slate-200 focus:border-indigo-400 outline-none px-1 bg-transparent"
                      />
                      <select
                        value={c.bloco_id}
                        onChange={e => moverClasse(c, parseInt(e.target.value))}
                        className="text-[10px] border border-slate-200 rounded px-1 py-0.5 bg-white outline-none"
                        title="Mover para outro bloco"
                      >
                        {blocosOrd.map(bb => <option key={bb.id} value={bb.id}>{bb.nome}</option>)}
                      </select>
                    </div>
                    {itensDaClasse(c.id).length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {itensDaClasse(c.id).map(t => (
                          <span key={t} className="group relative">
                            <select
                              value={c.id}
                              onChange={e => remapear(t, parseInt(e.target.value))}
                              className="text-[9px] bg-indigo-50 text-indigo-700 border border-indigo-100 rounded-full px-1.5 py-0.5 outline-none appearance-none cursor-pointer"
                              title={`${t} — mover para outra classificação`}
                            >
                              {classificacoes.map(cc => <option key={cc.id} value={cc.id}>{t} → {cc.nome}</option>)}
                            </select>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                <button onClick={() => novaClasse(b.id)} disabled={salvando}
                  className="text-[10px] font-bold text-indigo-500 hover:underline">+ classificação</button>
              </div>
            </div>
          ))}

          <button onClick={novoBloco} disabled={salvando}
            className="w-full py-2.5 border-2 border-dashed border-slate-200 rounded-xl text-xs font-bold text-slate-400 hover:border-slate-400 hover:text-slate-600">
            + Novo Bloco
          </button>

          <div className="text-[10px] text-slate-400 bg-slate-50 rounded-lg p-3">
            <b>Como funciona:</b> cada item do dimensionamento tem um <b>tipo</b> fixo (slug).
            A <b>classificação</b> agrupa tipos; o <b>bloco</b> agrupa classificações e aparece na proposta.
            Renomeie clicando no texto; mova uma classificação de bloco ou um item de classificação pelos seletores.
            As mudanças valem para orçamentos gerados a partir de agora.
          </div>
        </div>
      </div>
    </div>
  );
}
