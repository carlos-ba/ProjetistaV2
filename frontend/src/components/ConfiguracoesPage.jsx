import React, { useState, useEffect } from 'react';
import api from '../api';
import { useAuth } from '../contexts/AuthContext';

const DEFAULTS = {
  nome: 'Novo Perfil',
  tipo_filtro: 'solda',
  tipo_visor: 'solda',
  trecho_vet_evap: 0.5,
  trecho_evap_sifao: 0.5,
  trecho_subida: 1.0,
  trecho_sifao_gbc: 0.5,
  incluir_filtro: true,
  incluir_visor: true,
  incluir_gbc_entrada: true,
  incluir_gbc_saida: true,
  largura_aba_padrao_mm: 40,
  rendimento_selante_m_por_embalagem: 12.0,
};

const TRECHOS = [
  { campo: 'trecho_vet_evap',   label: 'VET → Evaporador' },
  { campo: 'trecho_evap_sifao', label: 'Evaporador → Sifão' },
  { campo: 'trecho_subida',     label: 'Sifão → Contra-sifão (subida)' },
  { campo: 'trecho_sifao_gbc',  label: 'Contra-sifão → GBC sucção' },
];

// Redimensiona a imagem do logo no próprio navegador (~400px no maior lado)
// antes de virar base64 — evita inchar o banco/payload com um arquivo grande.
const redimensionarLogo = (file, maxDim = 400) => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => {
    const img = new Image();
    img.onload = () => {
      const escala = Math.min(1, maxDim / Math.max(img.width, img.height));
      const w = Math.round(img.width * escala);
      const h = Math.round(img.height * escala);
      const canvas = document.createElement('canvas');
      canvas.width = w; canvas.height = h;
      canvas.getContext('2d').drawImage(img, 0, 0, w, h);
      resolve(canvas.toDataURL('image/png'));
    };
    img.onerror = () => reject(new Error('Não foi possível ler essa imagem.'));
    img.src = reader.result;
  };
  reader.onerror = () => reject(new Error('Não foi possível ler esse arquivo.'));
  reader.readAsDataURL(file);
});

// Fora do componente pai para que o React não recrie o tipo a cada render
function FormPerfil({ form, setForm, onSalvar, onCancelar, titulo, salvando, erro }) {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
      <p className="text-xs font-black text-slate-700 uppercase tracking-wide">{titulo}</p>

      <div>
        <label className="text-[10px] font-bold text-slate-500 uppercase">Nome do Perfil</label>
        <input
          className="w-full mt-1 border border-slate-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-slate-400"
          value={form.nome}
          onChange={e => setForm({ ...form, nome: e.target.value })}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        {[{ campo: 'tipo_filtro', label: 'Filtro Secador' }, { campo: 'tipo_visor', label: 'Visor de Líquido' }].map(({ campo, label }) => (
          <div key={campo}>
            <label className="text-[10px] font-bold text-slate-500 uppercase">{label}</label>
            <select
              value={form[campo]}
              onChange={e => setForm({ ...form, [campo]: e.target.value })}
              className="w-full mt-1 border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-slate-400"
            >
              <option value="solda">Solda</option>
              <option value="rosca">Rosca (flange + porca)</option>
            </select>
          </div>
        ))}
      </div>

      <div>
        <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">Componentes Incluídos</p>
        <div className="space-y-2">
          {[
            { campo: 'incluir_gbc_entrada', label: 'GBC entrada (linha de líquido)',   desc: 'Válvula globo na saída da condensadora' },
            { campo: 'incluir_filtro',      label: 'Filtro Secador',                   desc: 'DML/DMC — pode vir incluso na UC' },
            { campo: 'incluir_visor',       label: 'Visor de Líquido',                 desc: 'SGN — pode vir incluso na UC' },
            { campo: 'incluir_gbc_saida',   label: 'GBC saída (linha de sucção)',      desc: 'Válvula globo na entrada da condensadora' },
          ].map(({ campo, label, desc }) => (
            <div key={campo} className="flex items-center justify-between gap-3 py-1.5 border-b border-slate-100 last:border-0">
              <div>
                <p className="text-xs font-semibold text-slate-700">{label}</p>
                <p className="text-[10px] text-slate-400">{desc}</p>
              </div>
              <button
                type="button"
                onClick={() => setForm({ ...form, [campo]: !form[campo] })}
                className={`relative inline-flex h-5 w-9 flex-shrink-0 rounded-full border-2 border-transparent transition-colors focus:outline-none ${form[campo] ? 'bg-emerald-500' : 'bg-slate-200'}`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${form[campo] ? 'translate-x-4' : 'translate-x-0'}`} />
              </button>
            </div>
          ))}
        </div>
      </div>

      <div>
        <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">Trechos de Montagem (metros)</p>
        <div className="space-y-2">
          {TRECHOS.map(({ campo, label }) => (
            <div key={campo} className="flex items-center justify-between gap-2">
              <span className="text-xs text-gray-600">{label}</span>
              <input
                type="number" min="0.1" step="0.1"
                value={form[campo]}
                onChange={e => setForm({ ...form, [campo]: parseFloat(e.target.value) || 0 })}
                className="w-20 border border-slate-200 rounded px-2 py-1 text-xs text-center focus:outline-none focus:ring-1 focus:ring-slate-400"
              />
            </div>
          ))}
        </div>
      </div>

      <div>
        <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">Kit de Montagem (Card 1)</p>
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs text-gray-600">Largura de aba padrão (perfis)</span>
            <div className="flex items-center gap-1">
              <input
                type="number" min="1" step="1"
                value={form.largura_aba_padrao_mm}
                onChange={e => setForm({ ...form, largura_aba_padrao_mm: parseInt(e.target.value) || 0 })}
                className="w-20 border border-slate-200 rounded px-2 py-1 text-xs text-center focus:outline-none focus:ring-1 focus:ring-slate-400"
              />
              <span className="text-xs text-gray-400">mm</span>
            </div>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs text-gray-600">Rendimento do selante</span>
            <div className="flex items-center gap-1">
              <input
                type="number" min="0.1" step="0.1"
                value={form.rendimento_selante_m_por_embalagem}
                onChange={e => setForm({ ...form, rendimento_selante_m_por_embalagem: parseFloat(e.target.value) || 0 })}
                className="w-20 border border-slate-200 rounded px-2 py-1 text-xs text-center focus:outline-none focus:ring-1 focus:ring-slate-400"
              />
              <span className="text-xs text-gray-400">m/emb.</span>
            </div>
          </div>
        </div>
      </div>

      {erro && <p className="text-xs text-red-500">{erro}</p>}

      <div className="flex gap-2 pt-1">
        <button
          onClick={onSalvar} disabled={salvando}
          className="flex-1 py-2 bg-slate-800 text-white rounded-lg text-xs font-bold hover:bg-slate-700 disabled:opacity-50"
        >
          {salvando ? 'Salvando...' : 'Salvar'}
        </button>
        <button
          onClick={onCancelar}
          className="px-4 py-2 border border-slate-200 rounded-lg text-xs text-slate-600 hover:bg-slate-50"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}

export default function ConfiguracoesPage({ onFechar, onPerfilAtivo }) {
  const { user, atualizarModoEngenharia } = useAuth();
  const [perfis, setPerfis]     = useState([]);
  const [editando, setEditando] = useState(null);
  const [novoForm, setNovoForm] = useState(null);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro]         = useState('');
  const [salvandoModo, setSalvandoModo] = useState(false);

  // ── Identidade da Proposta ──────────────────────────────────────────
  const [identidade, setIdentidade] = useState({
    proposta_nome: '', proposta_logo_base64: '', proposta_contato_nome: '', proposta_contato_telefone: '',
  });
  const [salvandoIdentidade, setSalvandoIdentidade] = useState(false);
  const [erroIdentidade, setErroIdentidade] = useState('');
  const [sucessoIdentidade, setSucessoIdentidade] = useState(false);
  // Reflete o que está salvo no servidor (não o formulário em edição) — atualizado
  // só no carregamento e após salvar com sucesso, pra o botão indicar corretamente
  // "primeira vez" × "já existe uma identidade salva" mesmo depois de reabrir o modal.
  const [identidadeExistente, setIdentidadeExistente] = useState(false);

  useEffect(() => {
    api.get('/api/v1/configuracoes/identidade-proposta').then(r => {
      const dados = {
        proposta_nome: r.data.proposta_nome ?? '',
        proposta_logo_base64: r.data.proposta_logo_base64 ?? '',
        proposta_contato_nome: r.data.proposta_contato_nome ?? '',
        proposta_contato_telefone: r.data.proposta_contato_telefone ?? '',
      };
      setIdentidade(dados);
      setIdentidadeExistente(Object.values(dados).some(v => v));
    }).catch(() => {});
  }, []);

  const handleLogoSelecionado = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = ''; // permite escolher o mesmo arquivo de novo depois
    if (!file) return;
    setErroIdentidade('');
    try {
      const base64 = await redimensionarLogo(file);
      setIdentidade(v => ({ ...v, proposta_logo_base64: base64 }));
    } catch {
      setErroIdentidade('Não foi possível processar essa imagem.');
    }
  };

  const salvarIdentidade = async () => {
    setSalvandoIdentidade(true); setErroIdentidade(''); setSucessoIdentidade(false);
    try {
      await api.patch('/api/v1/configuracoes/identidade-proposta', identidade);
      setSucessoIdentidade(true);
      setIdentidadeExistente(true);
    } catch (err) {
      setErroIdentidade(err.response?.data?.detail?.[0]?.msg || 'Erro ao salvar a identidade da proposta.');
    } finally {
      setSalvandoIdentidade(false);
    }
  };

  const modoEngenharia = !!user?.modo_engenharia;
  const alternarModo = async (valor) => {
    setSalvandoModo(true);
    try { await atualizarModoEngenharia(valor); }
    catch { setErro('Erro ao salvar o modo do aplicativo.'); }
    finally { setSalvandoModo(false); }
  };

  const carregar = () =>
    api.get('/api/v1/configuracoes/montagem').then(r => setPerfis(r.data)).catch(() => {});

  useEffect(() => { carregar(); }, []);

  const ativar = async (id) => {
    await api.patch(`/api/v1/configuracoes/montagem/${id}/ativar`);
    await carregar();
    const ativo = perfis.find(p => p.id === id);
    if (ativo && onPerfilAtivo) onPerfilAtivo(ativo);
  };

  const salvarEdicao = async () => {
    if (!editando) return;
    setSalvando(true); setErro('');
    try {
      await api.put(`/api/v1/configuracoes/montagem/${editando.id}`, editando);
      await carregar();
      setEditando(null);
    } catch { setErro('Erro ao salvar.'); }
    finally { setSalvando(false); }
  };

  const criarPerfil = async () => {
    if (!novoForm) return;
    setSalvando(true); setErro('');
    try {
      await api.post('/api/v1/configuracoes/montagem', novoForm);
      await carregar();
      setNovoForm(null);
    } catch { setErro('Erro ao criar perfil.'); }
    finally { setSalvando(false); }
  };

  const deletar = async (id) => {
    if (!window.confirm('Excluir este perfil?')) return;
    await api.delete(`/api/v1/configuracoes/montagem/${id}`);
    carregar();
  };

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="absolute inset-0 bg-black/40" onClick={onFechar} />

      <div className="relative ml-auto w-full max-w-md bg-white h-full shadow-2xl flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 bg-slate-800">
          <div>
            <p className="text-sm font-black text-white">Configurações</p>
            <p className="text-[10px] text-slate-400">Identidade da proposta, modo do app e perfis de montagem</p>
          </div>
          <button onClick={onFechar} className="text-slate-400 hover:text-white text-xl leading-none">✕</button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4">

          {/* Identidade da Proposta — marca do técnico na proposta ao cliente */}
          <div className="rounded-xl border-2 border-[#7B2D8B]/30 bg-purple-50 p-4">
            <p className="text-[10px] font-black text-[#7B2D8B] uppercase tracking-widest mb-1">
              🏢 Identidade da Proposta
            </p>
            <p className="text-[11px] text-slate-500 mb-3">
              Aparece na proposta que você entrega ao seu cliente (Card 6) — nome, logo e contato.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Nome da Firma</label>
                <input
                  className="w-full mt-1 border border-slate-200 rounded-lg px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-[#7B2D8B]"
                  placeholder={user?.empresa_nome || 'Ex: WEM Refrigeração'}
                  value={identidade.proposta_nome}
                  onChange={e => setIdentidade(v => ({ ...v, proposta_nome: e.target.value }))}
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Logo</label>
                <div className="flex items-center gap-3">
                  {identidade.proposta_logo_base64 ? (
                    <img src={identidade.proposta_logo_base64} alt="Logo"
                      className="w-12 h-12 object-contain rounded-lg border border-slate-200 bg-white flex-shrink-0" />
                  ) : (
                    <div className="w-12 h-12 rounded-lg border border-dashed border-slate-300 flex items-center justify-center text-slate-300 text-xl flex-shrink-0">
                      +
                    </div>
                  )}
                  <label className="text-xs px-3 py-1.5 border border-slate-200 rounded-lg bg-white text-slate-600 hover:bg-slate-50 cursor-pointer">
                    {identidade.proposta_logo_base64 ? 'Trocar' : 'Escolher imagem'}
                    <input type="file" accept="image/*" className="hidden" onChange={handleLogoSelecionado} />
                  </label>
                  {identidade.proposta_logo_base64 && (
                    <button type="button" onClick={() => setIdentidade(v => ({ ...v, proposta_logo_base64: '' }))}
                      className="text-xs text-red-500 hover:underline">
                      Remover
                    </button>
                  )}
                </div>
                <p className="text-[10px] text-slate-400 mt-1">
                  PNG com fundo transparente, qualquer proporção — redimensionamos sozinhos, não precisa ser grande.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Nome do Contato</label>
                  <input
                    className="w-full mt-1 border border-slate-200 rounded-lg px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-[#7B2D8B]"
                    placeholder="Seu nome"
                    value={identidade.proposta_contato_nome}
                    onChange={e => setIdentidade(v => ({ ...v, proposta_contato_nome: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Celular do Contato</label>
                  <input
                    className="w-full mt-1 border border-slate-200 rounded-lg px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-[#7B2D8B]"
                    placeholder="(11) 91234-5678"
                    value={identidade.proposta_contato_telefone}
                    onChange={e => setIdentidade(v => ({ ...v, proposta_contato_telefone: e.target.value }))}
                  />
                </div>
              </div>

              {erroIdentidade && <p className="text-xs text-red-500">{erroIdentidade}</p>}
              {sucessoIdentidade && <p className="text-xs text-emerald-600">Identidade salva.</p>}

              <button onClick={salvarIdentidade} disabled={salvandoIdentidade}
                className={`w-full py-2 rounded-lg text-xs font-bold disabled:opacity-50 ${
                  identidadeExistente
                    ? 'border-2 border-[#7B2D8B] text-[#7B2D8B] bg-white hover:bg-purple-50'
                    : 'bg-[#7B2D8B] text-white hover:bg-purple-800'
                }`}>
                {salvandoIdentidade ? 'Salvando...' : (identidadeExistente ? 'Atualizar Identidade' : 'Salvar Identidade')}
              </button>
            </div>
          </div>

          {/* Modo do aplicativo (preferência do usuário) */}
          <div className="rounded-xl border-2 border-indigo-200 bg-indigo-50 p-4">
            <p className="text-[10px] font-black text-indigo-700 uppercase tracking-widest mb-2">Modo do aplicativo</p>
            <label className="flex items-start gap-3 cursor-pointer">
              <input type="checkbox" checked={modoEngenharia} disabled={salvandoModo}
                onChange={e => alternarModo(e.target.checked)}
                className="mt-0.5 w-4 h-4 accent-indigo-600" />
              <span className="text-sm text-slate-700">
                <span className="font-semibold">Somente engenharia</span>
                <span className="block text-xs text-slate-500">
                  App como gestor de engenharia: dimensionamento + lista de itens em Excel,
                  sem a jornada de orçamento (cotação, proposta, cliente e margens ficam ocultos).
                </span>
              </span>
            </label>
          </div>

          {perfis.map(p => (
            <div key={p.id} className={`rounded-xl border-2 p-4 ${p.ativo ? 'border-emerald-400 bg-emerald-50' : 'border-slate-200 bg-white'}`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  {p.ativo && <span className="text-[10px] font-black text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full uppercase">Ativo</span>}
                  <p className="text-sm font-bold text-slate-800">{p.nome}</p>
                </div>
                <div className="flex gap-1">
                  {!p.ativo && (
                    <button onClick={() => ativar(p.id)}
                      className="text-[10px] px-2 py-1 bg-emerald-600 text-white rounded-lg font-bold hover:bg-emerald-700">
                      Ativar
                    </button>
                  )}
                  <button onClick={() => setEditando({ ...p })}
                    className="text-[10px] px-2 py-1 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50">
                    Editar
                  </button>
                  {perfis.length > 1 && (
                    <button onClick={() => deletar(p.id)}
                      className="text-[10px] px-2 py-1 border border-red-200 rounded-lg text-red-500 hover:bg-red-50">
                      ✕
                    </button>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px] text-slate-600 mb-2">
                <span>Filtro: <b className="capitalize">{p.tipo_filtro}</b></span>
                <span>Visor: <b className="capitalize">{p.tipo_visor}</b></span>
                <span>VET→Evap: <b>{p.trecho_vet_evap} m</b></span>
                <span>Evap→Sifão: <b>{p.trecho_evap_sifao} m</b></span>
                <span>Subida: <b>{p.trecho_subida} m</b></span>
                <span>C-Sifão→GBC: <b>{p.trecho_sifao_gbc} m</b></span>
                <span>Aba padrão: <b>{p.largura_aba_padrao_mm ?? 40} mm</b></span>
                <span>Selante: <b>{p.rendimento_selante_m_por_embalagem ?? 12} m/emb.</b></span>
              </div>
              <div className="flex flex-wrap gap-1">
                {[
                  { key: 'incluir_gbc_entrada', label: 'GBC entrada' },
                  { key: 'incluir_filtro',      label: 'Filtro' },
                  { key: 'incluir_visor',       label: 'Visor' },
                  { key: 'incluir_gbc_saida',   label: 'GBC saída' },
                ].map(({ key, label }) => (
                  <span key={key} className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${p[key] !== false ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-500 line-through'}`}>
                    {label}
                  </span>
                ))}
              </div>

              {editando?.id === p.id && (
                <div className="mt-4">
                  <FormPerfil
                    form={editando} setForm={setEditando}
                    onSalvar={salvarEdicao} onCancelar={() => setEditando(null)}
                    titulo="Editar Perfil" salvando={salvando} erro={erro}
                  />
                </div>
              )}
            </div>
          ))}

          {novoForm ? (
            <FormPerfil
              form={novoForm} setForm={setNovoForm}
              onSalvar={criarPerfil} onCancelar={() => setNovoForm(null)}
              titulo="Novo Perfil" salvando={salvando} erro={erro}
            />
          ) : (
            <button
              onClick={() => setNovoForm({ ...DEFAULTS })}
              className="w-full py-3 border-2 border-dashed border-slate-200 rounded-xl text-xs font-bold text-slate-400 hover:border-slate-400 hover:text-slate-600 transition-all"
            >
              + Novo Perfil de Montagem
            </button>
          )}

          <div className="text-[10px] text-slate-400 bg-slate-50 rounded-lg p-3">
            <b>Dica:</b> O perfil <b>Ativo</b> é carregado automaticamente ao iniciar qualquer projeto.
            Você pode ter perfis diferentes para cada tipo de instalação (industrial, comercial, etc.)
            e alternar conforme o projeto.
          </div>
        </div>
      </div>
    </div>
  );
}
