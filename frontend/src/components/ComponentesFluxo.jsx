import React, { useState, useEffect } from 'react';
import api from '../api';

const COMPONENTES_SEGURANCA = [
  { id: 'quadro_eletrico',     label: 'Quadro Elétrico' },
  { id: 'separador_oleo',      label: 'Separador de Óleo' },
  { id: 'pressostato_alta',    label: 'Pressostato de Alta' },
  { id: 'pressostato_baixa',   label: 'Pressostato de Baixa' },
];

const ComponentesFluxo = ({ cargaAlvo, fluido, tempEvap, aoFinalizar }) => {
  const [componentes, setComponentes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState('');
  const [selecionados, setSelecionados] = useState({});
  const [seguranca, setSeguranca] = useState(
    Object.fromEntries(COMPONENTES_SEGURANCA.map(c => [c.id, false]))
  );

  const buscarComponentes = async () => {
    setLoading(true);
    setErro('');
    try {
      const response = await api.post('/api/v1/selecionar-componentes-fluxo/', {
        capacidade_kcalh: cargaAlvo,
        fluido: fluido,
        temp_evap: tempEvap
      });
      setComponentes(response.data);
      
      // Pré-seleciona todos por padrão
      const initial = {};
      response.data.forEach(c => {
        initial[c.categoria] = true;
      });
      setSelecionados(initial);
    } catch (error) {
      console.error(error);
      setErro('Erro ao buscar componentes de fluxo.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (cargaAlvo > 0) {
      buscarComponentes();
    }
  }, [cargaAlvo, fluido, tempEvap]);

  const toggleSelecao = (categoria) => {
    setSelecionados(prev => ({
      ...prev,
      [categoria]: !prev[categoria]
    }));
  };

  const finalizar = () => {
    const itensParaEnviar = componentes
      .filter(c => selecionados[c.categoria])
      .map(c => ({
        item: `${c.categoria} ${c.modelo}`,
        quantidade: 1,
        unidade: 'un',
        detalhe: `${c.fabricante} | ${c.conexao_entrada} | ${c.faixa_operacao}`,
        custo_unitario: c.custo, // Se o orçamento precisar do custo
        preco: c.custo // Compatibilidade com GeradorOrcamento
      }));

    if (aoFinalizar) {
      aoFinalizar(itensParaEnviar);
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500 font-bold animate-pulse">⚙️ Dimensionando acessórios de fluxo...</div>;
  if (erro) return <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-100">{erro}</div>;

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden transition-all hover:shadow-xl">
      <div className="bg-gradient-to-r from-[#7B2D8B] to-[#6BBF3F] px-6 py-4 flex justify-between items-center">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span className="bg-white/20 p-1.5 rounded-lg text-lg">🔧</span>
          Componentes de Fluxo e Segurança
        </h2>
        <div className="text-[10px] text-white/80 font-bold bg-white/20 px-3 py-1 rounded-full uppercase">
          Dimensionamento Automático
        </div>
      </div>

      <div className="p-6">
        <div className="mb-6 p-4 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between">
           <div>
              <span className="text-[10px] font-black text-slate-400 uppercase">Referência de Projeto</span>
              <div className="text-sm font-bold text-slate-700">
                {cargaAlvo} kcal/h | {fluido} | {tempEvap}°C Evap.
              </div>
           </div>
           <button 
             onClick={buscarComponentes}
             className="text-xs font-bold text-emerald-600 hover:text-emerald-700 underline"
           >
             Recalcular Acessórios
           </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {componentes.map((comp, idx) => (
            <div 
              key={idx}
              onClick={() => toggleSelecao(comp.categoria)}
              className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex items-start gap-4 ${
                selecionados[comp.categoria] 
                  ? 'border-emerald-500 bg-emerald-50 shadow-sm' 
                  : 'border-slate-100 bg-white opacity-60 grayscale hover:grayscale-0 hover:opacity-100'
              }`}
            >
              <div className={`mt-1 w-5 h-5 rounded flex items-center justify-center text-[10px] font-black ${
                selecionados[comp.categoria] ? 'bg-emerald-500 text-white' : 'bg-slate-200 text-slate-400'
              }`}>
                {selecionados[comp.categoria] ? '✓' : ''}
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <span className={`text-[10px] font-black uppercase ${
                    selecionados[comp.categoria] ? 'text-emerald-600' : 'text-slate-400'
                  }`}>
                    {comp.categoria}
                  </span>
                  <span className="text-xs font-bold text-slate-900">R$ {comp.custo.toLocaleString('pt-BR')}</span>
                </div>
                <h4 className="font-bold text-slate-800">{comp.modelo}</h4>
                <div className="text-[10px] text-slate-500 font-medium mt-1">
                  {comp.fabricante} | {comp.conexao_entrada} | {comp.faixa_operacao}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* CHECKLIST DE SEGURANÇA */}
        <div className="mt-6">
          <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">
            Componentes de Segurança
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {COMPONENTES_SEGURANCA.map(comp => (
              <div
                key={comp.id}
                onClick={() => setSeguranca(prev => ({ ...prev, [comp.id]: !prev[comp.id] }))}
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex items-center gap-4 ${
                  seguranca[comp.id]
                    ? 'border-emerald-500 bg-emerald-50 shadow-sm'
                    : 'border-slate-100 bg-white hover:border-slate-300'
                }`}
              >
                <div className={`w-5 h-5 rounded flex-shrink-0 flex items-center justify-center text-[10px] font-black ${
                  seguranca[comp.id] ? 'bg-emerald-500 text-white' : 'bg-slate-200 text-slate-400'
                }`}>
                  {seguranca[comp.id] ? '✓' : ''}
                </div>
                <div className="flex-1">
                  <span className="font-bold text-slate-800 text-sm">{comp.label}</span>
                  <span className={`ml-2 text-[9px] font-black uppercase px-2 py-0.5 rounded-full ${
                    seguranca[comp.id]
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-slate-100 text-slate-400'
                  }`}>
                    {seguranca[comp.id] ? 'Selecionado' : 'Não Selecionado'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={finalizar}
          className="w-full mt-8 py-4 bg-[#7B2D8B] text-white rounded-xl font-bold hover:bg-purple-800 transition-all flex items-center justify-center gap-2 shadow-lg shadow-purple-200"
        >
          CONFIRMAR ACESSÓRIOS E IR PARA TUBULAÇÃO ➡️
        </button>
      </div>
    </div>
  );
};

export default ComponentesFluxo;
