import React, { useState, useEffect } from 'react';
import api from '../api';

const TIPOS = [
  { id: 'Unidade Condensadora', label: 'U. Condensadora', icone: '🧊' },
  { id: 'Evaporadora',          label: 'Evaporadora',     icone: '❄️' },
];

const SelecaoEquipamentos = ({ cargaInicial, tempInterna, tempAmb = 35, onDeltaTChange, aoFinalizar }) => {
  const [cargaTotal, setCargaTotal] = useState(2000);
  const [numMaquinas, setNumMaquinas] = useState(1);
  const [deltaT, setDeltaT] = useState('');
  const [evap, setEvap] = useState('');
  const [cond, setCond] = useState(tempAmb + 10);
  const [fluido, setFluido] = useState('R22');
  const [abaAtiva, setAbaAtiva] = useState('Unidade Condensadora');

  // resultados separados por tipo
  const [resultadosUC,   setResultadosUC]   = useState([]);
  const [resultadosEvap, setResultadosEvap] = useState([]);
  const [quantidades,    setQuantidades]    = useState({});
  const [selecionados,   setSelecionados]   = useState([]);
  const [loading,        setLoading]        = useState(false);
  const [erro,           setErro]           = useState('');

  const cargaReferencia = Math.round(cargaTotal / numMaquinas);
  const resultadosAtivos = abaAtiva === 'Unidade Condensadora' ? resultadosUC : resultadosEvap;

  useEffect(() => {
    if (cargaInicial && cargaInicial > 0) setCargaTotal(Math.round(cargaInicial));
  }, [cargaInicial]);

  useEffect(() => {
    setCond(tempAmb + 10);
  }, [tempAmb]);

  useEffect(() => {
    const tInt = parseFloat(tempInterna);
    const dt   = parseFloat(deltaT);
    if (!isNaN(tInt) && !isNaN(dt)) setEvap(tInt - dt);
    else setEvap('');
    if (onDeltaTChange) onDeltaTChange(isNaN(dt) ? null : dt);
  }, [tempInterna, deltaT]);

  const buscarEquipamentos = async () => {
    const evapVal = parseFloat(evap);
    if (isNaN(evapVal)) {
      setErro('Informe o Delta T para calcular a temperatura de evaporação antes de buscar.');
      return;
    }
    setLoading(true);
    setErro('');
    setResultadosUC([]);
    setResultadosEvap([]);
    setQuantidades({});

    const params = {
      carga_termica_total: cargaReferencia,
      temp_evaporacao:     evapVal,
      temp_condensacao:    cond,
      fluido,
    };

    try {
      const [resUC, resEvap] = await Promise.all([
        api.post('/api/v1/selecao', { ...params, tipo: 'Unidade Condensadora' }),
        api.post('/api/v1/selecao', { ...params, tipo: 'Evaporadora' }),
      ]);

      setResultadosUC(resUC.data);
      setResultadosEvap(resEvap.data);

      const initialQtys = {};
      [...resUC.data, ...resEvap.data].forEach(item => {
        initialQtys[item.id] = numMaquinas;
      });
      setQuantidades(initialQtys);

      if (resUC.data.length === 0 && resEvap.data.length === 0)
        setErro('Nenhum equipamento compatível encontrado no catálogo.');
    } catch {
      setErro('Erro de conexão com o servidor.');
    } finally {
      setLoading(false);
    }
  };

  const atualizarQuantidade = (id, valor) => {
    setQuantidades(prev => ({ ...prev, [id]: Math.max(1, parseInt(valor) || 1) }));
  };

  const adicionarAoRascunho = (item) => {
    const qtd = quantidades[item.id] || 1;
    setSelecionados(prev => [...prev, {
      nome:              `${item.modelo} (${item.fabricante})`,
      preco:             item.preco,
      qtde:              qtd,
      detalhe:           `${item.capacidade_real} kcal/h`,
      capacidade_real:   item.capacidade_real,
      vazao_ar:          item.vazao_ar,
      fluido,
      temp_evap:         evap,
      temp_cond:         cond,
      modelo:            item.modelo,
      id:                item.id,
      categoria:         abaAtiva,
      volume_interno_kg: item.volume_interno_kg ?? null,
      conexao_liquido:   item.conexao_liquido   ?? null,
      conexao_succao:    item.conexao_succao     ?? null,
    }]);
  };

  const removerDoRascunho = (idx) => {
    setSelecionados(prev => prev.filter((_, i) => i !== idx));
  };

  const finalizarEtapa = () => {
    if (selecionados.length === 0) {
      alert('Selecione pelo menos um equipamento antes de avançar.');
      return;
    }
    if (aoFinalizar) aoFinalizar(selecionados);
  };

  const jaAdicionado = (item) => selecionados.some(s => s.id === item.id || s.modelo === item.modelo);

  const temResultados = resultadosUC.length > 0 || resultadosEvap.length > 0;

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden transition-all hover:shadow-xl">
      <div className="bg-gradient-to-r from-[#7B2D8B] to-[#6BBF3F] px-6 py-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span className="bg-white/20 p-1.5 rounded-lg text-lg">⚙️</span>
          3. Seleção de Equipamentos
        </h2>
      </div>

      <div className="p-6">

        {/* Parâmetros */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase">Carga Total (kcal/h)</label>
            <input type="number" value={cargaTotal} onChange={e => setCargaTotal(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all" />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase">Nº Equipamentos</label>
            <input type="number" min="1" value={numMaquinas}
              onChange={e => setNumMaquinas(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full px-4 py-2 rounded-lg border border-blue-200 bg-blue-50 font-bold text-blue-700 focus:ring-2 focus:ring-blue-500 outline-none transition-all" />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase">Ref. p/ Máquina</label>
            <div className="w-full px-4 py-2 rounded-lg border border-slate-200 bg-slate-50 font-black text-slate-700">
              {cargaReferencia} <small className="font-normal text-[9px]">kcal/h</small>
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase">Delta T (°C)</label>
            <input type="number" value={deltaT} onChange={e => setDeltaT(e.target.value)} placeholder="Ex: 6"
              className="w-full px-4 py-2 rounded-lg border border-blue-200 bg-blue-50 font-bold text-blue-700 focus:ring-2 focus:ring-blue-500 outline-none transition-all" />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase">T. Evap (°C)</label>
            <input type="number" value={evap} onChange={e => setEvap(e.target.value)} placeholder="Calculada automaticamente"
              className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all" />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase">T. Condensação estimada</label>
            <div className="w-full px-4 py-2 rounded-lg border border-amber-200 bg-amber-50 font-black text-amber-700 text-sm">
              {cond}°C
              <div className="text-[9px] font-normal text-amber-600 leading-tight mt-0.5">
                T.Amb {tempAmb}°C + 10°C (padrão de mercado)
              </div>
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase">Fluido</label>
            <select value={fluido} onChange={e => setFluido(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none bg-white">
              <option value="R22">R22</option>
              <option value="R404A">R404A</option>
            </select>
          </div>
        </div>

        <button onClick={buscarEquipamentos} disabled={loading}
          className={`w-full py-3 rounded-lg font-bold shadow transition-all mb-6 ${
            loading ? 'bg-slate-300 cursor-not-allowed' : 'bg-[#7B2D8B] hover:bg-purple-800 text-white'
          }`}>
          {loading ? 'Buscando...' : '🔍 BUSCAR NO CATÁLOGO'}
        </button>

        {erro && <div className="p-4 bg-amber-50 text-amber-700 border border-amber-200 rounded-lg text-sm mb-6">{erro}</div>}

        {/* Abas + resultados */}
        {temResultados && (
          <div className="mb-6">

            {/* Abas */}
            <div className="flex border-b border-slate-200 mb-4">
              {TIPOS.map(t => {
                const qtdResultados = t.id === 'Unidade Condensadora' ? resultadosUC.length : resultadosEvap.length;
                const qtdSelecionados = selecionados.filter(s => s.categoria === t.id).length;
                const ativa = abaAtiva === t.id;
                return (
                  <button
                    key={t.id}
                    onClick={() => setAbaAtiva(t.id)}
                    className={`flex items-center gap-2 px-5 py-3 text-sm font-bold border-b-2 transition-all ${
                      ativa
                        ? 'border-[#7B2D8B] text-[#7B2D8B]'
                        : 'border-transparent text-slate-400 hover:text-slate-600'
                    }`}
                  >
                    <span>{t.icone}</span>
                    <span>{t.label}</span>
                    {qtdResultados > 0 && (
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-black ${
                        ativa ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-500'
                      }`}>
                        {qtdResultados}
                      </span>
                    )}
                    {qtdSelecionados > 0 && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-black bg-emerald-100 text-emerald-700">
                        ✓ {qtdSelecionados}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Cards da aba ativa */}
            <div className="flex gap-6 overflow-x-auto pb-4 scrollbar-thin scrollbar-thumb-slate-200 scrollbar-track-transparent">
              {resultadosAtivos.length === 0 ? (
                <div className="w-full py-8 text-center text-slate-400 text-sm">
                  Nenhum equipamento encontrado para este tipo.
                </div>
              ) : resultadosAtivos.map((item, idx) => {
                const perc = (item.capacidade_real / cargaReferencia) * 100;
                let statusCor = 'ideal';
                let label = '✅ Capacidade Ideal';
                if (perc < 90) { statusCor = 'menor'; label = '⚠️ Capacidade Menor'; }
                else if (perc > 110) { statusCor = 'maior'; label = '🔵 Sobredimensionado'; }

                const adicionado = jaAdicionado(item);

                return (
                  <div key={idx} className={`min-w-[280px] flex flex-col rounded-2xl border-2 transition-all p-5 ${
                    adicionado
                      ? 'border-emerald-500 bg-emerald-50 ring-4 ring-emerald-50 shadow-lg'
                      : statusCor === 'ideal'
                        ? 'border-emerald-200 bg-white hover:border-emerald-400'
                        : statusCor === 'menor'
                          ? 'border-amber-200 bg-white hover:border-amber-400'
                          : 'border-blue-200 bg-white hover:border-blue-400'
                  }`}>
                    <div className="mb-4">
                      <span className={`text-[10px] font-black uppercase px-2 py-1 rounded-full ${
                        statusCor === 'ideal' ? 'bg-emerald-100 text-emerald-700'
                        : statusCor === 'menor' ? 'bg-amber-100 text-amber-700'
                        : 'bg-blue-100 text-blue-700'
                      }`}>
                        {label}
                      </span>
                      <h4 className="text-lg font-bold text-slate-800 mt-2 line-clamp-1">{item.modelo}</h4>
                      <p className="text-xs text-slate-500 font-medium uppercase tracking-tighter">{item.fabricante}</p>
                    </div>

                    <div className="flex-1 space-y-3">
                      <div className="flex items-baseline gap-1">
                        <span className="text-2xl font-black text-slate-900">{item.capacidade_real}</span>
                        <span className="text-xs font-bold text-slate-400 uppercase">kcal/h</span>
                      </div>
                      <div className="text-xl font-bold text-blue-600">R$ {item.preco.toLocaleString('pt-BR')}</div>

                      <div className="mt-4 pt-4 border-t border-slate-100">
                        <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Quantidade de Unidades</label>
                        <div className="flex items-center gap-2">
                          <button onClick={() => atualizarQuantidade(item.id, (quantidades[item.id] || 1) - 1)}
                            className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold">−</button>
                          <input type="number" value={quantidades[item.id] || 1}
                            onChange={e => atualizarQuantidade(item.id, e.target.value)}
                            className="w-12 text-center font-bold text-slate-800 bg-transparent outline-none" />
                          <button onClick={() => atualizarQuantidade(item.id, (quantidades[item.id] || 1) + 1)}
                            className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold">+</button>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => adicionarAoRascunho(item)}
                      disabled={adicionado}
                      className={`mt-6 w-full py-3 rounded-xl font-bold transition-all border-2 flex items-center justify-center gap-2 ${
                        adicionado
                          ? 'bg-emerald-500 border-emerald-500 text-white cursor-not-allowed'
                          : 'border-[#7B2D8B] text-[#7B2D8B] hover:bg-[#7B2D8B] hover:text-white'
                      }`}>
                      {adicionado ? (
                        <><span className="text-lg">✓</span> Selecionado</>
                      ) : (
                        <><span className="text-lg">✓</span> Selecionar</>
                      )}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Lista de selecionados */}
        {selecionados.length > 0 && (
          <div className="mt-4 border-t border-slate-100 pt-6 animate-in fade-in duration-500">
            <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
              <span className="text-emerald-500">✓</span> Equipamentos Selecionados
            </h3>

            <div className="overflow-hidden border border-slate-200 rounded-xl mb-6">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="px-4 py-3 text-sm font-bold text-slate-600">Equipamento</th>
                    <th className="px-4 py-3 text-sm font-bold text-slate-600">Detalhe</th>
                    <th className="px-4 py-3 text-sm font-bold text-slate-600 text-right">Ação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {selecionados.map((s, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="text-[10px] font-black text-slate-400 uppercase mb-0.5">{s.categoria}</div>
                        <div className="font-bold text-slate-800">{s.nome}</div>
                        <div className="text-xs text-blue-600 font-bold">
                          {s.qtde} x R$ {s.preco.toLocaleString('pt-BR')} = R$ {(s.qtde * s.preco).toLocaleString('pt-BR')}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-500 text-sm">
                        {s.detalhe}{s.qtde > 1 && ` (Total: ${s.qtde * s.capacidade_real} kcal/h)`}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button onClick={() => removerDoRascunho(idx)}
                          className="text-red-500 hover:text-red-700 p-2 hover:bg-red-50 rounded-lg transition-all">
                          🗑️
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button onClick={finalizarEtapa}
              className="w-full py-4 bg-[#7B2D8B] hover:bg-purple-800 text-white font-black rounded-xl shadow-lg shadow-purple-200 transition-all hover:-translate-y-1 active:translate-y-0">
              FINALIZAR SELEÇÃO E CONTINUAR ➡️
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SelecaoEquipamentos;
