import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import api from '../api';
import CatalogoPrecosEmpresa from './CatalogoPrecosEmpresa';

/**
 * Administração IceNexus — gestão de empresas (tenants) e seus usuários.
 *
 * Visível apenas para o papel superadmin_icenexus. É por aqui que a implantação
 * de um cliente empresa é feita: cria-se a empresa e os usuários da equipe dela.
 */

const PLANOS = [
  { id: 'trial',    label: 'Trial' },
  { id: 'tecnico',  label: 'Técnico (individual)' },
  { id: 'empresa',  label: 'Empresa (multiusuário)' },
];

const STATUS = [
  { id: 'ativa',     label: 'Ativa',     cor: 'bg-emerald-100 text-emerald-700' },
  { id: 'suspensa',  label: 'Suspensa',  cor: 'bg-amber-100 text-amber-700' },
  { id: 'cancelada', label: 'Cancelada', cor: 'bg-red-100 text-red-600' },
];

const PAPEIS = [
  { id: 'admin_empresa', label: 'Administrador' },
  { id: 'membro',        label: 'Membro' },
];

const badgeStatus = (s) => (STATUS.find(x => x.id === s) || STATUS[0]).cor;
const empresaVazia = { nome: '', cnpj: '', plano: 'empresa', status_assinatura: 'ativa' };
const usuarioVazio = { username: '', email: '', password: '', papel: 'membro' };

export default function AdminEmpresas({ aberto, aoFechar }) {
  const [empresas, setEmpresas]   = useState([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro]           = useState('');
  const [ok, setOk]               = useState('');

  const [novaEmpresa, setNovaEmpresa]   = useState(null);
  const [editando, setEditando]         = useState(null);
  const [expandida, setExpandida]       = useState(null);   // empresa_id com equipe aberta
  const [expandidaCatalogo, setExpandidaCatalogo] = useState(null); // empresa_id com catálogo de preços aberto
  const [usuarios, setUsuarios]         = useState({});     // empresa_id -> lista
  const [novoUsuario, setNovoUsuario]   = useState(null);   // { empresa_id, ...campos }
  const [editUsuario, setEditUsuario]   = useState(null);   // { empresa_id, id, email, password }
  const [salvando, setSalvando]         = useState(false);

  const carregar = async () => {
    setCarregando(true); setErro('');
    try {
      const { data } = await api.get('/api/v1/admin/empresas');
      setEmpresas(data);
    } catch (e) {
      setErro(e.response?.status === 403
        ? 'Acesso restrito à administração IceNexus.'
        : 'Erro ao carregar empresas.');
    } finally { setCarregando(false); }
  };

  useEffect(() => { if (aberto) { carregar(); setOk(''); } }, [aberto]);

  const aviso = (msg) => { setOk(msg); setTimeout(() => setOk(''), 4000); };
  const msgErro = (e, padrao) => {
    const d = e.response?.data?.detail;
    if (typeof d === 'string') return d;
    if (d && typeof d === 'object') return Object.values(d).flat().join(' · ');
    return padrao;
  };

  const criarEmpresa = async () => {
    if (!novaEmpresa?.nome.trim()) { setErro('Informe o nome da empresa.'); return; }
    setSalvando(true); setErro('');
    try {
      await api.post('/api/v1/admin/empresas', novaEmpresa);
      setNovaEmpresa(null); await carregar(); aviso('Empresa criada.');
    } catch (e) { setErro(msgErro(e, 'Erro ao criar empresa.')); }
    finally { setSalvando(false); }
  };

  const salvarEmpresa = async () => {
    setSalvando(true); setErro('');
    try {
      const { id, nome, cnpj, plano, status_assinatura } = editando;
      await api.patch(`/api/v1/admin/empresas/${id}`, { nome, cnpj, plano, status_assinatura });
      setEditando(null); await carregar(); aviso('Empresa atualizada.');
    } catch (e) { setErro(msgErro(e, 'Erro ao salvar.')); }
    finally { setSalvando(false); }
  };

  const abrirEquipe = async (id) => {
    if (expandida === id) { setExpandida(null); return; }
    setExpandida(id); setErro('');
    try {
      const { data } = await api.get(`/api/v1/admin/empresas/${id}/usuarios`);
      setUsuarios(u => ({ ...u, [id]: data }));
    } catch { setErro('Erro ao carregar a equipe.'); }
  };

  const criarUsuario = async () => {
    const { empresa_id, ...dados } = novoUsuario;
    if (!dados.username.trim() || !dados.email.trim() || dados.password.length < 8) {
      setErro('Preencha usuário, e-mail e senha com ao menos 8 caracteres.'); return;
    }
    setSalvando(true); setErro('');
    try {
      await api.post(`/api/v1/admin/empresas/${empresa_id}/usuarios`, dados);
      setNovoUsuario(null);
      const { data } = await api.get(`/api/v1/admin/empresas/${empresa_id}/usuarios`);
      setUsuarios(u => ({ ...u, [empresa_id]: data }));
      await carregar(); aviso('Usuário criado.');
    } catch (e) { setErro(msgErro(e, 'Erro ao criar usuário.')); }
    finally { setSalvando(false); }
  };

  // Um só caminho para ativar/desativar e trocar papel — desativar precisa ser
  // reversível, já que username e e-mail são únicos e o usuário não pode ser recriado.
  const atualizarUsuario = async (empresa_id, uid, dados, confirmacao) => {
    if (confirmacao && !window.confirm(confirmacao)) return;
    setErro('');
    try {
      await api.patch(`/api/v1/admin/usuarios/${uid}`, dados);
      const { data } = await api.get(`/api/v1/admin/empresas/${empresa_id}/usuarios`);
      setUsuarios(u => ({ ...u, [empresa_id]: data }));
      aviso(dados.is_active === false ? 'Acesso desativado.'
          : dados.is_active === true ? 'Acesso reativado.'
          : 'Papel atualizado.');
    } catch (e) { setErro(msgErro(e, 'Erro ao atualizar usuário.')); }
  };

  const salvarUsuario = async () => {
    const { empresa_id, id, email, password } = editUsuario;
    const dados = {};
    if (email && email !== editUsuario.emailOriginal) dados.email = email;
    if (password) {
      if (password.length < 8) { setErro('A senha deve ter ao menos 8 caracteres.'); return; }
      dados.password = password;
    }
    if (!Object.keys(dados).length) { setEditUsuario(null); return; }
    setSalvando(true); setErro('');
    try {
      await api.patch(`/api/v1/admin/usuarios/${id}`, dados);
      const { data } = await api.get(`/api/v1/admin/empresas/${empresa_id}/usuarios`);
      setUsuarios(u => ({ ...u, [empresa_id]: data }));
      setEditUsuario(null);
      aviso(dados.password ? 'Senha redefinida — informe-a ao usuário.' : 'Cadastro atualizado.');
    } catch (e) { setErro(msgErro(e, 'Erro ao salvar usuário.')); }
    finally { setSalvando(false); }
  };

  if (!aberto) return null;

  const campo = "w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none focus:ring-2 focus:ring-indigo-400";

  return createPortal(
    <div className="fixed inset-0 z-50 flex bg-black/40" onClick={aoFechar}>
      <div className="relative ml-auto w-full max-w-3xl bg-slate-50 h-full shadow-2xl flex flex-col"
           onClick={e => e.stopPropagation()}>

        {/* Cabeçalho */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-900 flex-shrink-0">
          <div>
            <p className="text-sm font-black text-white">🏢 Administração IceNexus</p>
            <p className="text-[10px] text-slate-400">Empresas assinantes e suas equipes</p>
          </div>
          <button onClick={aoFechar} className="text-slate-400 hover:text-white text-xl leading-none">✕</button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4">

          {erro && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 font-semibold">{erro}</div>}
          {ok   && <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-700 font-semibold">✓ {ok}</div>}

          {/* Nova empresa */}
          {novaEmpresa ? (
            <div className="bg-white rounded-xl border-2 border-indigo-200 p-4 space-y-3">
              <h4 className="text-xs font-black text-indigo-700 uppercase">Nova empresa</h4>
              <div className="grid grid-cols-2 gap-3">
                <input className={campo} placeholder="Razão social *" value={novaEmpresa.nome}
                  onChange={e => setNovaEmpresa(v => ({ ...v, nome: e.target.value }))} />
                <input className={campo} placeholder="CNPJ" value={novaEmpresa.cnpj}
                  onChange={e => setNovaEmpresa(v => ({ ...v, cnpj: e.target.value }))} />
                <select className={campo} value={novaEmpresa.plano}
                  onChange={e => setNovaEmpresa(v => ({ ...v, plano: e.target.value }))}>
                  {PLANOS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
                </select>
                <select className={campo} value={novaEmpresa.status_assinatura}
                  onChange={e => setNovaEmpresa(v => ({ ...v, status_assinatura: e.target.value }))}>
                  {STATUS.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
                </select>
              </div>
              <div className="flex gap-2 justify-end">
                <button onClick={() => { setNovaEmpresa(null); setErro(''); }}
                  className="text-xs px-4 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50">Cancelar</button>
                <button onClick={criarEmpresa} disabled={salvando}
                  className="text-xs px-4 py-2 rounded-lg bg-indigo-600 text-white font-bold hover:bg-indigo-700 disabled:opacity-50">
                  {salvando ? 'Criando...' : 'Criar empresa'}
                </button>
              </div>
            </div>
          ) : (
            <button onClick={() => { setNovaEmpresa({ ...empresaVazia }); setErro(''); }}
              className="w-full py-3 rounded-xl border-2 border-dashed border-indigo-300 text-indigo-600 font-bold text-sm hover:bg-indigo-50 transition-colors">
              + Nova empresa
            </button>
          )}

          {carregando && <p className="text-center text-sm text-slate-400 py-6 animate-pulse">Carregando...</p>}

          {/* Lista */}
          {empresas.map(e => (
            <div key={e.id} className="bg-white rounded-xl border border-slate-200 overflow-hidden">

              {editando?.id === e.id ? (
                <div className="p-4 space-y-3 bg-amber-50/40">
                  <div className="grid grid-cols-2 gap-3">
                    <input className={campo} value={editando.nome || ''}
                      onChange={ev => setEditando(v => ({ ...v, nome: ev.target.value }))} />
                    <input className={campo} placeholder="CNPJ" value={editando.cnpj || ''}
                      onChange={ev => setEditando(v => ({ ...v, cnpj: ev.target.value }))} />
                    <select className={campo} value={editando.plano}
                      onChange={ev => setEditando(v => ({ ...v, plano: ev.target.value }))}>
                      {PLANOS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
                    </select>
                    <select className={campo} value={editando.status_assinatura}
                      onChange={ev => setEditando(v => ({ ...v, status_assinatura: ev.target.value }))}>
                      {STATUS.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
                    </select>
                  </div>
                  <div className="flex gap-2 justify-end">
                    <button onClick={() => setEditando(null)}
                      className="text-xs px-4 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50">Cancelar</button>
                    <button onClick={salvarEmpresa} disabled={salvando}
                      className="text-xs px-4 py-2 rounded-lg bg-slate-800 text-white font-bold hover:bg-slate-900 disabled:opacity-50">Salvar</button>
                  </div>
                </div>
              ) : (
                <div className="p-4 flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-bold text-slate-800">{e.nome}</p>
                      <span className={`text-[9px] font-black px-2 py-0.5 rounded-full uppercase ${badgeStatus(e.status_assinatura)}`}>
                        {e.status_assinatura}
                      </span>
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 uppercase">
                        {e.plano}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {e.cnpj || 'sem CNPJ'} · {e.total_usuarios} usuário{e.total_usuarios === 1 ? '' : 's'}
                    </p>
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    <button onClick={() => abrirEquipe(e.id)}
                      className="text-[10px] px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 font-bold border border-indigo-200 hover:bg-indigo-100">
                      {expandida === e.id ? 'Fechar' : 'Equipe'}
                    </button>
                    <button onClick={() => setExpandidaCatalogo(v => v === e.id ? null : e.id)}
                      className="text-[10px] px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 font-bold border border-emerald-200 hover:bg-emerald-100">
                      {expandidaCatalogo === e.id ? 'Fechar' : '📦 Catálogo'}
                    </button>
                    <button onClick={() => { setEditando({ ...e }); setErro(''); }}
                      className="text-[10px] px-2.5 py-1 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50">Editar</button>
                  </div>
                </div>
              )}

              {/* Equipe */}
              {expandida === e.id && (
                <div className="border-t border-slate-100 bg-slate-50/60 p-4 space-y-2">
                  {(usuarios[e.id] || []).map(u => (
                    <React.Fragment key={u.id}>
                    <div className={`flex items-center justify-between rounded-lg px-3 py-2 border ${
                      u.is_active ? 'bg-white border-slate-100' : 'bg-slate-100/70 border-slate-200'}`}>
                      <div className="min-w-0">
                        <p className={`text-sm font-semibold ${u.is_active ? 'text-slate-800' : 'text-slate-400 line-through'}`}>
                          {u.username}
                          {!u.is_active && (
                            <span className="ml-2 text-[9px] font-black px-1.5 py-0.5 rounded-full bg-red-100 text-red-600 uppercase no-underline inline-block align-middle">
                              inativo
                            </span>
                          )}
                        </p>
                        <p className="text-[10px] text-slate-400 flex items-center gap-1.5 flex-wrap">
                          {u.email}
                          {u.is_active && (
                            <span className="text-slate-300">
                              · {u.sessoes_ativas} sess{u.sessoes_ativas === 1 ? 'ão' : 'ões'} ativa{u.sessoes_ativas === 1 ? '' : 's'}
                              {u.ips_distintos_hoje > 1 && (
                                <span className="ml-1 text-amber-600 font-semibold" title="IP é um sinal ruidoso (técnico de campo troca de rede várias vezes por dia) — use como subsídio, não como prova.">
                                  · {u.ips_distintos_hoje} IPs distintos/24h
                                </span>
                              )}
                            </span>
                          )}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <select value={u.papel} disabled={!u.is_active}
                          onChange={ev => atualizarUsuario(e.id, u.id, { papel: ev.target.value })}
                          title="Papel na empresa"
                          className="text-[10px] font-bold px-1.5 py-0.5 rounded-lg border border-slate-200 bg-white text-slate-600 outline-none disabled:opacity-50">
                          {PAPEIS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
                        </select>
                        <button
                          onClick={() => { setEditUsuario({ empresa_id: e.id, id: u.id, email: u.email, emailOriginal: u.email, password: '' }); setErro(''); }}
                          className="text-[10px] px-2 py-1 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
                          title="Alterar e-mail ou redefinir senha">Editar</button>
                        {u.is_active ? (
                          <button
                            onClick={() => atualizarUsuario(e.id, u.id, { is_active: false },
                              `Desativar o acesso de "${u.username}"? Ele poderá ser reativado depois.`)}
                            className="text-[10px] px-2 py-1 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 border border-transparent hover:border-red-200"
                            title="Desativar acesso">Desativar</button>
                        ) : (
                          <button
                            onClick={() => atualizarUsuario(e.id, u.id, { is_active: true })}
                            className="text-[10px] px-2 py-1 rounded-lg bg-emerald-50 text-emerald-700 font-bold border border-emerald-200 hover:bg-emerald-100"
                            title="Reativar acesso">Reativar</button>
                        )}
                      </div>
                    </div>
                    {editUsuario?.id === u.id && (
                      <div className="bg-white rounded-lg border-2 border-amber-200 p-3 space-y-2 -mt-1">
                        <p className="text-[10px] font-black text-amber-700 uppercase">Editar {u.username}</p>
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <label className="text-[9px] font-bold text-slate-400 uppercase block mb-0.5">E-mail</label>
                            <input className={campo} value={editUsuario.email}
                              onChange={ev => setEditUsuario(v => ({ ...v, email: ev.target.value }))} />
                          </div>
                          <div>
                            <label className="text-[9px] font-bold text-slate-400 uppercase block mb-0.5">Nova senha</label>
                            <input className={campo} placeholder="deixe em branco para manter"
                              value={editUsuario.password}
                              onChange={ev => setEditUsuario(v => ({ ...v, password: ev.target.value }))} />
                          </div>
                        </div>
                        <p className="text-[10px] text-slate-400">
                          A senha definida aqui passa a valer imediatamente — anote e entregue ao usuário.
                        </p>
                        <div className="flex gap-2 justify-end">
                          <button onClick={() => { setEditUsuario(null); setErro(''); }}
                            className="text-[11px] px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50">Cancelar</button>
                          <button onClick={salvarUsuario} disabled={salvando}
                            className="text-[11px] px-3 py-1.5 rounded-lg bg-amber-600 text-white font-bold hover:bg-amber-700 disabled:opacity-50">
                            {salvando ? 'Salvando...' : 'Salvar'}
                          </button>
                        </div>
                      </div>
                    )}
                    </React.Fragment>
                  ))}
                  {(usuarios[e.id] || []).length === 0 && (
                    <p className="text-xs text-slate-400 italic">Nenhum usuário nesta empresa.</p>
                  )}

                  {novoUsuario?.empresa_id === e.id ? (
                    <div className="bg-white rounded-lg border-2 border-indigo-200 p-3 space-y-2 mt-2">
                      <div className="grid grid-cols-2 gap-2">
                        <input className={campo} placeholder="usuário *" value={novoUsuario.username}
                          onChange={ev => setNovoUsuario(v => ({ ...v, username: ev.target.value }))} />
                        <input className={campo} placeholder="e-mail *" type="email" value={novoUsuario.email}
                          onChange={ev => setNovoUsuario(v => ({ ...v, email: ev.target.value }))} />
                        <input className={campo} placeholder="senha (mín. 8) *" value={novoUsuario.password}
                          onChange={ev => setNovoUsuario(v => ({ ...v, password: ev.target.value }))} />
                        <select className={campo} value={novoUsuario.papel}
                          onChange={ev => setNovoUsuario(v => ({ ...v, papel: ev.target.value }))}>
                          {PAPEIS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
                        </select>
                      </div>
                      <p className="text-[10px] text-slate-400">
                        A senha é definida agora e entregue ao usuário — ele já entra sem confirmar e-mail.
                      </p>
                      <div className="flex gap-2 justify-end">
                        <button onClick={() => { setNovoUsuario(null); setErro(''); }}
                          className="text-[11px] px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50">Cancelar</button>
                        <button onClick={criarUsuario} disabled={salvando}
                          className="text-[11px] px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-bold hover:bg-indigo-700 disabled:opacity-50">
                          {salvando ? 'Criando...' : 'Criar usuário'}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button onClick={() => { setNovoUsuario({ empresa_id: e.id, ...usuarioVazio }); setErro(''); }}
                      className="text-xs font-bold text-indigo-600 hover:underline mt-1">
                      + Adicionar usuário
                    </button>
                  )}
                </div>
              )}

              {/* Catálogo de preços — implantação (superadmin cadastra pela empresa) */}
              {expandidaCatalogo === e.id && (
                <div className="border-t border-slate-100 bg-emerald-50/30 p-4">
                  <p className="text-[10px] text-slate-400 mb-2">
                    Lista de preços de <b>{e.nome}</b> — o cliente também pode editar isso
                    sozinho, em "Catálogo de Preços" no menu dele.
                  </p>
                  <CatalogoPrecosEmpresa apiBase={`/api/v1/admin/empresas/${e.id}/produtos`} />
                </div>
              )}
            </div>
          ))}

          {!carregando && empresas.length === 0 && !erro && (
            <p className="text-center text-sm text-slate-400 py-8">Nenhuma empresa cadastrada.</p>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}
