import React, { useState, useEffect } from 'react';
import api from '../api';

const PADROES = [
  { id: 'D', faixa: '6–7,5 mm',   desc: '≥ 0°C'         },
  { id: 'F', faixa: '9–12 mm',    desc: '-5°C a 0°C'    },
  { id: 'H', faixa: '13–16 mm',   desc: '-15°C a -5°C'  },
  { id: 'M', faixa: '19–26 mm',   desc: '-25°C a -15°C' },
  { id: 'R', faixa: '25–32,5 mm', desc: '-35°C a -25°C' },
  { id: 'T', faixa: '32–45 mm',   desc: '< -35°C'       },
];

const CalculadoraTubulacao = ({ evaporador, condensadora, aoFinalizar, initialValues, onValoresChange, jaFinalizado = false, invalidado = false }) => {
  const [distancia,      setDistancia]     = useState(initialValues?.distancia      ?? 5);
  const [altaEficiencia, setAltaEficiencia]= useState(initialValues?.altaEficiencia ?? false);
  const [deltaT,         setDeltaT]        = useState(initialValues?.deltaT         ?? 6);
  const [padrao,         setPadrao]        = useState(initialValues?.padrao         ?? 'H');
  const [isolarLiquido,  setIsolarLiquido] = useState(initialValues?.isolarLiquido  ?? false);

  const [sugestao,       setSugestao]      = useState(null);
  const [bitolas,        setBitolas]       = useState(null);
  const [resultado,      setResultado]     = useState(initialValues?.resultado ?? null);

  useEffect(() => {
    if (onValoresChange) onValoresChange({ distancia, altaEficiencia, deltaT, padrao, isolarLiquido, resultado });
  }, [distancia, altaEficiencia, deltaT, padrao, isolarLiquido, resultado]);
  const [erro,           setErro]          = useState('');
  const [loading,        setLoading]       = useState(false);

  // Evaporador é a referência primária para o cálculo de tubulação
  const base = evaporador ?? condensadora;

  // Alerta de desbalanço: diferença > 15% entre evaporador e condensadora
  const desbalanco = evaporador && condensadora
    ? Math.abs(evaporador.capacidade_real - condensadora.capacidade_real) / Math.max(evaporador.capacidade_real, condensadora.capacidade_real)
    : 0;

  useEffect(() => {
    const tEvap = base?.temp_evap;
    if (tEvap == null) return;
    api.get(`/api/v1/tubulacao/sugestao-isolamento?temp_evap=${tEvap}`)
      .then(r => { setSugestao(r.data); setPadrao(r.data.padrao); })
      .catch(() => {});
  }, [base?.temp_evap]);

  const resetarEtapas = () => { setBitolas(null); setResultado(null); };

  if (!base) {
    return (
      <div className="p-8 bg-amber-50 border-2 border-dashed border-amber-200 rounded-2xl text-center">
        <span className="text-3xl mb-3 block">⚠️</span>
        <h3 className="text-amber-800 font-bold">Aguardando Seleção</h3>
        <p className="text-amber-600 text-sm mt-1">Selecione os equipamentos no passo anterior.</p>
      </div>
    );
  }

  const payload = () => ({
    capacidade_real:     base.capacidade_real || 2000,
    fluido:              base.fluido || 'R22',
    temp_evap:           base.temp_evap || -10,
    distancia:           parseFloat(distancia),
    alta_eficiencia:     altaEficiencia,
    delta_t_selecionado: deltaT,
    padrao_isolamento:   padrao,
    isolar_liquido:      isolarLiquido,
    num_circuitos:       base.qtde || 1,
  });

  const calcularBitolas = async () => {
    setLoading(true); setErro(''); setResultado(null);
    try {
      const r = await api.post('/api/v1/tubulacao', payload());
      setBitolas(r.data);
    } catch {
      setErro('Erro ao calcular tubulação.');
    } finally {
      setLoading(false);
    }
  };

  const gerarMateriais = async () => {
    setLoading(true); setErro('');
    try {
      const r = await api.post('/api/v1/tubulacao', payload());
      setResultado(r.data);
      if (aoFinalizar) aoFinalizar(r.data.lista_materiais, r.data);
    } catch {
      setErro('Erro ao gerar lista de materiais.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
      <div className="bg-gradient-to-r from-cyan-600 to-blue-700 px-6 py-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span className="bg-white/20 p-1.5 rounded-lg text-lg">🔩</span>
          Dimensionamento de Tubulação
        </h2>
      </div>

      <div className="p-6 space-y-6">
        {/* Banner dados alterados upstream */}
        {invalidado && (
          <div className="p-3 bg-amber-50 border border-amber-300 rounded-xl flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="text-sm font-semibold text-amber-800">Equipamentos foram alterados</p>
              <p className="text-xs text-amber-600">Recalcule as bitolas de tubulação para o novo dimensionamento</p>
            </div>
          </div>
        )}

        {/* Equipamentos do sistema */}
        <div className="space-y-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">

            {/* Evaporador */}
            <div className={`p-3 rounded-xl border-2 ${evaporador ? 'bg-teal-50 border-teal-200' : 'bg-slate-50 border-dashed border-slate-200'}`}>
              <span className="text-[10px] font-black text-teal-500 uppercase">Evaporador · base do cálculo</span>
              {evaporador ? (
                <>
                  <div className="font-bold text-slate-700 mt-0.5">{evaporador.modelo}</div>
                  <div className="text-sm text-teal-700 font-medium">
                    {evaporador.capacidade_real} kcal/h | {evaporador.fluido} | T.Evap: {evaporador.temp_evap}°C
                  </div>
                </>
              ) : (
                <div className="text-xs text-slate-400 mt-1">Não selecionado</div>
              )}
            </div>

            {/* Unidade Condensadora */}
            <div className={`p-3 rounded-xl border-2 ${condensadora ? 'bg-blue-50 border-blue-200' : 'bg-slate-50 border-dashed border-slate-200'}`}>
              <span className="text-[10px] font-black text-blue-500 uppercase">U. Condensadora · referência</span>
              {condensadora ? (
                <>
                  <div className="font-bold text-slate-700 mt-0.5">{condensadora.modelo}</div>
                  <div className="text-sm text-blue-700 font-medium">
                    {condensadora.capacidade_real} kcal/h | {condensadora.fluido}
                  </div>
                </>
              ) : (
                <div className="text-xs text-slate-400 mt-1">Não selecionada</div>
              )}
            </div>
          </div>

          {/* Alerta de desbalanço */}
          {desbalanco > 0.15 && (
            <div className="flex items-start gap-2 bg-amber-50 border border-amber-300 rounded-lg px-3 py-2 text-xs text-amber-800">
              <span className="text-base leading-none">⚠️</span>
              <span>
                <strong>Desbalanço de {Math.round(desbalanco * 100)}%</strong> entre evaporador e condensadora.
                O cálculo usa a capacidade do evaporador ({evaporador?.capacidade_real} kcal/h).
                Verifique se os equipamentos são compatíveis.
              </span>
            </div>
          )}
        </div>

        {/* ETAPA 1 — Parâmetros de dimensionamento */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-black flex items-center justify-center flex-shrink-0">1</span>
            <span className="text-sm font-black text-slate-700 uppercase tracking-wide">Parâmetros de Dimensionamento</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-500 uppercase">Distância (m)</label>
              <input type="number" value={distancia}
                onChange={e => { setDistancia(e.target.value); resetarEtapas(); }}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none text-sm" />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-500 uppercase">Delta T Evap.</label>
              <select value={deltaT}
                onChange={e => { setDeltaT(e.target.value); resetarEtapas(); }}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                {[6,7,8,9,10,11,12].map(v => <option key={v} value={v}>{v}K</option>)}
              </select>
            </div>
            <div className="flex items-end col-span-2 md:col-span-2">
              <label className={`w-full flex items-center justify-between px-3 py-2 rounded-lg border-2 cursor-pointer transition-all text-sm ${altaEficiencia ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-slate-200 text-slate-500'}`}>
                <div>
                  <span className="font-bold block">Sucção Otimizada</span>
                  <span className="text-[10px] opacity-70">Sobe uma bitola — menor ΔP</span>
                </div>
                <input type="checkbox" checked={altaEficiencia}
                  onChange={e => { setAltaEficiencia(e.target.checked); resetarEtapas(); }}
                  className="w-4 h-4 accent-emerald-600" />
              </label>
            </div>
          </div>

          {/* Banner projeto carregado */}
          {jaFinalizado && !resultado && (
            <div className="mb-2 p-3 bg-green-50 border border-green-200 rounded-xl flex items-center gap-3">
              <span className="text-2xl">✅</span>
              <div>
                <p className="text-sm font-semibold text-green-800">Tubulação dimensionada — dados carregados do arquivo</p>
                <p className="text-xs text-green-600">Clique em "Recalcular" para atualizar os resultados detalhados</p>
              </div>
            </div>
          )}

          <button onClick={calcularBitolas} disabled={loading}
            className={`w-full py-3 rounded-xl font-bold text-white shadow-lg transition-all ${
              loading ? 'bg-slate-300'
              : jaFinalizado && !resultado ? 'bg-green-600 hover:bg-green-700 hover:-translate-y-0.5'
              : 'bg-gradient-to-br from-blue-600 to-indigo-700 hover:shadow-blue-200 hover:-translate-y-0.5'
            }`}>
            {loading && !bitolas ? 'Calculando...'
              : jaFinalizado && !resultado ? '🔄 Recalcular Bitolas'
              : 'CALCULAR BITOLAS ➡️'}
          </button>
        </div>

        {erro && <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm border border-red-100">{erro}</div>}

        {/* ETAPA 2 — Bitolas + Acessórios + Isolamento */}
        {bitolas && (
          <div className="space-y-6 animate-in zoom-in-95 duration-300">

            {/* Resultado das bitolas */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-teal-600 text-white text-xs font-black flex items-center justify-center flex-shrink-0">2</span>
                <span className="text-sm font-black text-slate-700 uppercase tracking-wide">Bitolas Calculadas</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 p-4 rounded-2xl border-2 border-blue-100 text-center">
                  <span className="text-[10px] font-black text-blue-400 uppercase tracking-widest">Linha de Líquido</span>
                  <div className="text-3xl font-black text-blue-900 mt-1">{bitolas.diametro_liquido}</div>
                  <p className="text-xs text-blue-600 mt-1 font-medium">Alta Pressão</p>
                </div>
                <div className="bg-teal-50 p-4 rounded-2xl border-2 border-teal-100 text-center">
                  <span className="text-[10px] font-black text-teal-400 uppercase tracking-widest">Linha de Sucção</span>
                  <div className="text-3xl font-black text-teal-900 mt-1">{bitolas.diametro_succao}</div>
                  <p className="text-xs text-teal-600 mt-1 font-medium">Baixa Pressão</p>
                </div>
              </div>
            </div>

            {/* Conexões e Acessórios */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-black flex items-center justify-center flex-shrink-0">3</span>
                <span className="text-sm font-black text-slate-700 uppercase tracking-wide">Conexões e Acessórios</span>
              </div>
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

                  <div className="flex items-end pb-6">
                    <label className={`w-full flex items-center justify-between px-3 py-2 rounded-lg border-2 cursor-pointer transition-all text-sm ${isolarLiquido ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 text-slate-500'}`}>
                      <div>
                        <span className="font-bold block">Isolar Líquido</span>
                        <span className="text-[10px] opacity-70">Linha {bitolas.diametro_liquido}</span>
                      </div>
                      <input type="checkbox" checked={isolarLiquido}
                        onChange={e => { setIsolarLiquido(e.target.checked); setResultado(null); }}
                        className="w-4 h-4 accent-blue-600" />
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Padrão de Isolamento */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-violet-600 text-white text-xs font-black flex items-center justify-center flex-shrink-0">4</span>
                <span className="text-sm font-black text-slate-700 uppercase tracking-wide">Padrão de Isolamento Armacel</span>
                {sugestao && (
                  <span className="text-[10px] bg-violet-200 text-violet-800 font-bold px-2 py-1 rounded-full ml-auto">
                    💡 Sugerido: {sugestao.padrao} ({sugestao.faixa_espessura})
                  </span>
                )}
              </div>
              <div className="bg-violet-50 border border-violet-200 rounded-xl p-4">
                <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                  {PADROES.map(p => (
                    <button
                      key={p.id}
                      onClick={() => { setPadrao(p.id); setResultado(null); }}
                      className={`rounded-lg p-2 text-center border-2 transition-all ${
                        padrao === p.id
                          ? 'border-[#7B2D8B] bg-[#7B2D8B] text-white shadow-md'
                          : sugestao?.padrao === p.id
                            ? 'border-violet-400 bg-violet-100 text-violet-800'
                            : 'border-slate-200 bg-white text-slate-600 hover:border-violet-300'
                      }`}
                    >
                      <div className="text-lg font-black">{p.id}</div>
                      <div className="text-[9px] font-bold leading-tight">{p.faixa}</div>
                      <div className="text-[8px] opacity-70 leading-tight mt-0.5">{p.desc}</div>
                      {sugestao?.padrao === p.id && padrao !== p.id && (
                        <div className="text-[8px] text-violet-600 font-black mt-0.5">sugerido</div>
                      )}
                    </button>
                  ))}
                </div>
                {sugestao && (
                  <p className="text-[10px] text-violet-600 mt-2 italic">{sugestao.justificativa}</p>
                )}
              </div>
            </div>

            {/* Botão gerar materiais */}
            <button onClick={gerarMateriais} disabled={loading}
              className={`w-full py-3.5 rounded-xl font-bold text-white shadow-lg transition-all ${
                loading ? 'bg-slate-300' : 'bg-gradient-to-br from-violet-600 to-indigo-700 hover:shadow-violet-200 hover:-translate-y-0.5'
              }`}>
              {loading ? 'Gerando...' : 'GERAR LISTA DE MATERIAIS ➡️'}
            </button>

            {/* ETAPA 3 — Lista de materiais */}
            {resultado && (
              <div className="space-y-4 animate-in zoom-in-95 duration-300">

                <div className="bg-slate-50 rounded-xl border border-slate-200 overflow-hidden">
                  <div className="px-4 py-2 bg-slate-100 border-b border-slate-200">
                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                      Materiais — Isolamento Padrão {resultado.padrao_isolamento_usado}
                    </span>
                  </div>
                  <div className="divide-y divide-slate-100">
                    {resultado.lista_materiais.map((m, i) => (
                      <div key={i} className="flex items-center justify-between px-4 py-2">
                        <div>
                          <p className="text-sm font-bold text-slate-700">{m.item}</p>
                          <p className="text-[10px] text-slate-400">{m.detalhe}</p>
                        </div>
                        <span className="text-sm font-black text-slate-900 ml-4 whitespace-nowrap">
                          {m.quantidade} {m.unidade}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-100 text-emerald-700 text-sm font-bold flex items-center gap-2">
                  <span>✅</span> Tubulação e isolamento adicionados à lista de materiais!
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CalculadoraTubulacao;
