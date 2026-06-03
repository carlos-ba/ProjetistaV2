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

const CalculadoraTubulacao = ({ equipamentoSelecionado, aoFinalizar }) => {
  const [distancia,      setDistancia]     = useState(5);
  const [altaEficiencia, setAltaEficiencia]= useState(false);
  const [deltaT,         setDeltaT]        = useState(6);
  const [padrao,         setPadrao]        = useState('H');
  const [isolarLiquido,  setIsolarLiquido] = useState(false);
  const [numCurvas90,    setNumCurvas90]   = useState('');    // vazio = automático
  const [incluirSifao,   setIncluirSifao]  = useState(true);
  const [sugestao,       setSugestao]      = useState(null);
  const [resultado,      setResultado]     = useState(null);
  const [erro,           setErro]          = useState('');
  const [loading,        setLoading]       = useState(false);

  // Busca sugestão automática quando T.Evap do equipamento está disponível
  useEffect(() => {
    const tEvap = equipamentoSelecionado?.temp_evap;
    if (tEvap == null) return;
    api.get(`/api/v1/tubulacao/sugestao-isolamento?temp_evap=${tEvap}`)
      .then(r => {
        setSugestao(r.data);
        setPadrao(r.data.padrao);
      })
      .catch(() => {});
  }, [equipamentoSelecionado?.temp_evap]);

  if (!equipamentoSelecionado) {
    return (
      <div className="p-8 bg-amber-50 border-2 border-dashed border-amber-200 rounded-2xl text-center">
        <span className="text-3xl mb-3 block">⚠️</span>
        <h3 className="text-amber-800 font-bold">Aguardando Seleção</h3>
        <p className="text-amber-600 text-sm mt-1">Selecione um equipamento no passo anterior.</p>
      </div>
    );
  }

  const calcular = async () => {
    setLoading(true); setErro('');
    try {
      const response = await api.post('/api/v1/tubulacao', {
        capacidade_real:      equipamentoSelecionado.capacidade_real || 2000,
        fluido:               equipamentoSelecionado.fluido || 'R22',
        temp_evap:            equipamentoSelecionado.temp_evap || -10,
        distancia:            parseFloat(distancia),
        alta_eficiencia:      altaEficiencia,
        delta_t_selecionado:  deltaT,
        padrao_isolamento:    padrao,
        isolar_liquido:       isolarLiquido,
        num_circuitos:        equipamentoSelecionado.qtde || 1,
        num_curvas_90:        numCurvas90 !== '' ? parseInt(numCurvas90) : null,
        incluir_sifao:        incluirSifao,
      });
      setResultado(response.data);
      if (aoFinalizar) aoFinalizar(response.data.lista_materiais);
    } catch (error) {
      setErro('Erro ao calcular tubulação.');
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

        {/* Equipamento base */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
          <span className="text-[10px] font-black text-slate-400 uppercase">Equipamento Base</span>
          <div className="font-bold text-slate-700">{equipamentoSelecionado.modelo}</div>
          <div className="text-sm text-blue-600 font-medium">
            {equipamentoSelecionado.capacidade_real} kcal/h | {equipamentoSelecionado.fluido} | T.Evap: {equipamentoSelecionado.temp_evap}°C
          </div>
        </div>

        {/* Parâmetros */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-bold text-slate-500 uppercase">Distância (m)</label>
            <input type="number" value={distancia} onChange={e => setDistancia(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none text-sm" />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-bold text-slate-500 uppercase">Delta T Evap.</label>
            <select value={deltaT} onChange={e => setDeltaT(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
              {[6,7,8,9,10,11,12].map(v => <option key={v} value={v}>{v}K</option>)}
            </select>
          </div>
          <div className="flex items-end">
            <label className={`w-full flex items-center justify-between px-3 py-2 rounded-lg border-2 cursor-pointer transition-all text-sm ${altaEficiencia ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-slate-200 text-slate-500'}`}>
              <span className="font-bold">Alta Eficiência</span>
              <input type="checkbox" checked={altaEficiencia} onChange={e => setAltaEficiencia(e.target.checked)}
                className="w-4 h-4 accent-emerald-600" />
            </label>
          </div>
          <div className="flex items-end">
            <label className={`w-full flex items-center justify-between px-3 py-2 rounded-lg border-2 cursor-pointer transition-all text-sm ${isolarLiquido ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 text-slate-500'}`}>
              <div>
                <span className="font-bold block">Isolar Líquido</span>
                <span className="text-[10px] opacity-70">Caso especial</span>
              </div>
              <input type="checkbox" checked={isolarLiquido} onChange={e => setIsolarLiquido(e.target.checked)}
                className="w-4 h-4 accent-blue-600" />
            </label>
          </div>
        </div>

        {/* Conexões */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
          <h3 className="text-sm font-black text-slate-700 mb-3">🔗 Conexões e Acessórios</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-500 uppercase">
                Curvas 90°
                <span className="font-normal text-slate-400 ml-1 normal-case">(vazio = automático)</span>
              </label>
              <input
                type="number" min="0" value={numCurvas90}
                onChange={e => setNumCurvas90(e.target.value)}
                placeholder={`Auto (${
                  parseFloat(distancia) <= 10 ? 2 :
                  parseFloat(distancia) <= 20 ? 4 :
                  parseFloat(distancia) <= 40 ? 6 :
                  parseFloat(distancia) <= 60 ? 8 : 10
                } estimado)`}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-400 outline-none"
              />
              <p className="text-[10px] text-slate-400">
                Curvas 45° = metade das 90° | Uniões = igual às 90°
              </p>
            </div>

            <div className="flex items-end pb-6">
              <label className={`w-full flex items-center justify-between px-3 py-2 rounded-lg border-2 cursor-pointer transition-all text-sm ${incluirSifao ? 'border-blue-400 bg-blue-50 text-blue-700' : 'border-slate-200 text-slate-500'}`}>
                <div>
                  <span className="font-bold block">Sifão + Contra-sifão</span>
                  <span className="text-[10px] opacity-70">Saída do evaporador</span>
                </div>
                <input type="checkbox" checked={incluirSifao} onChange={e => setIncluirSifao(e.target.checked)}
                  className="w-4 h-4 accent-blue-600" />
              </label>
            </div>

            <div className="flex items-end pb-6">
              <label className={`w-full flex items-center justify-between px-3 py-2 rounded-lg border-2 cursor-pointer transition-all text-sm ${isolarLiquido ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 text-slate-500'}`}>
                <div>
                  <span className="font-bold block">Isolar Líquido</span>
                  <span className="text-[10px] opacity-70">Caso especial</span>
                </div>
                <input type="checkbox" checked={isolarLiquido} onChange={e => setIsolarLiquido(e.target.checked)}
                  className="w-4 h-4 accent-blue-600" />
              </label>
            </div>
          </div>
        </div>

        {/* Seleção de padrão de isolamento */}
        <div className="bg-violet-50 border border-violet-200 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-black text-violet-800">🧊 Padrão de Isolamento Armacel</h3>
            {sugestao && (
              <span className="text-[10px] bg-violet-200 text-violet-800 font-bold px-2 py-1 rounded-full">
                💡 Sugerido: {sugestao.padrao} ({sugestao.faixa_espessura})
              </span>
            )}
          </div>

          <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
            {PADROES.map(p => (
              <button
                key={p.id}
                onClick={() => setPadrao(p.id)}
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

        {/* Botão calcular */}
        <button onClick={calcular} disabled={loading}
          className={`w-full py-3.5 rounded-xl font-bold text-white shadow-lg transition-all ${
            loading ? 'bg-slate-300' : 'bg-gradient-to-br from-blue-600 to-indigo-700 hover:shadow-blue-200 hover:-translate-y-0.5'
          }`}>
          {loading ? 'Dimensionando...' : 'CALCULAR TUBULAÇÃO E ISOLAMENTO ➡️'}
        </button>

        {erro && <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm border border-red-100">{erro}</div>}

        {/* Resultado */}
        {resultado && (
          <div className="space-y-4 animate-in zoom-in-95 duration-300">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 p-4 rounded-2xl border-2 border-blue-100 text-center">
                <span className="text-[10px] font-black text-blue-400 uppercase tracking-widest">Linha de Líquido</span>
                <div className="text-3xl font-black text-blue-900 mt-1">{resultado.diametro_liquido}</div>
                <p className="text-xs text-blue-600 mt-1 font-medium">Alta Pressão</p>
              </div>
              <div className="bg-teal-50 p-4 rounded-2xl border-2 border-teal-100 text-center">
                <span className="text-[10px] font-black text-teal-400 uppercase tracking-widest">Linha de Sucção</span>
                <div className="text-3xl font-black text-teal-900 mt-1">{resultado.diametro_succao}</div>
                <p className="text-xs text-teal-600 mt-1 font-medium">Com Isolamento</p>
              </div>
            </div>

            {/* Info conexões */}
            <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 text-xs text-blue-700">
              <span className="font-bold">Conexões: </span>
              {resultado.curvas_90_usadas} curvas 90° + {Math.floor(resultado.curvas_90_usadas / 2)} curvas 45°
              {incluirSifao && ' + sifão + contra-sifão (sucção)'}
              <span className="text-blue-400 ml-2">— {resultado.origem_curvas}</span>
            </div>

            {/* Lista de materiais */}
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
    </div>
  );
};

export default CalculadoraTubulacao;
