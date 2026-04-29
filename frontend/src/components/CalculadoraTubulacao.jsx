import React, { useState } from 'react';
import api from '../api';

const CalculadoraTubulacao = ({ equipamentoSelecionado, aoFinalizar }) => {
  const [distancia, setDistancia] = useState(5);
  const [altaEficiencia, setAltaEficiencia] = useState(false);
  const [metodo, setMetodo] = useState('tabela');
  const [deltaT, setDeltaT] = useState(6);

  const [resultado, setResultado] = useState(null);
  const [erro, setErro] = useState('');
  const [loading, setLoading] = useState(false);

  if (!equipamentoSelecionado) {
    return (
      <div className="p-8 bg-amber-50 border-2 border-dashed border-amber-200 rounded-2xl text-center">
        <span className="text-3xl mb-3 block">⚠️</span>
        <h3 className="text-amber-800 font-bold">Aguardando Seleção</h3>
        <p className="text-amber-600 text-sm mt-1">Por favor, selecione uma Unidade Condensadora no passo anterior.</p>
      </div>
    );
  }

  const calcular = async () => {
    setLoading(true);
    setErro('');
    try {
      const response = await api.post('/api/v1/calcular-tubulacao/', {
        capacidade_real: equipamentoSelecionado.capacidade_real || 2000,
        fluido: equipamentoSelecionado.fluido || 'R22',
        temp_evap: equipamentoSelecionado.temp_evap || -10,
        distancia: parseFloat(distancia),
        alta_eficiencia: altaEficiencia,
        metodo: metodo,
        delta_t_selecionado: deltaT
      });

      setResultado(response.data);
      if (aoFinalizar) aoFinalizar(response.data.lista_materiais);
    } catch (error) {
      console.error(error);
      setErro('Erro ao calcular tubulação.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden transition-all hover:shadow-xl">
      <div className="bg-gradient-to-r from-cyan-600 to-blue-700 px-6 py-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span className="bg-white/20 p-1.5 rounded-lg text-lg">🧪</span>
          4. Dimensionamento de Tubulação
        </h2>
      </div>

      <div className="p-6">
        <div className="flex flex-col md:flex-row gap-4 mb-8">
           <div className="flex-1 bg-slate-50 p-4 rounded-xl border border-slate-100">
              <span className="text-[10px] font-black text-slate-400 uppercase">Equipamento Base</span>
              <div className="font-bold text-slate-700">{equipamentoSelecionado.modelo}</div>
              <div className="text-sm text-blue-600 font-medium">{equipamentoSelecionado.capacidade_real} kcal/h | {equipamentoSelecionado.fluido}</div>
           </div>
           
           <div className="flex-[2] grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-500 uppercase">Metodo</label>
                <div className="flex bg-slate-100 p-1 rounded-lg">
                  <button onClick={()=>setMetodo('tabela')} className={`flex-1 py-1.5 text-xs font-bold rounded-md transition-all ${metodo === 'tabela' ? 'bg-white shadow-sm text-blue-600' : 'text-slate-500'}`}>Tabela</button>
                  <button className="flex-1 py-1.5 text-xs font-bold text-slate-300 cursor-not-allowed">Cálculo (Em breve)</button>
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-500 uppercase">Delta T (Evaporação)</label>
                <select value={deltaT} onChange={e => setDeltaT(e.target.value)} className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                   {[6,7,8,9,10,11,12].map(v => <option key={v} value={v}>{v}K</option>)}
                </select>
              </div>
           </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 items-end">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Distância Linear (m)</label>
            <input 
              type="number" value={distancia} onChange={e => setDistancia(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
          </div>

          <div className="flex items-center gap-3">
             <label className={`flex-1 flex items-center justify-between px-4 py-3 rounded-xl border-2 cursor-pointer transition-all ${altaEficiencia ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-slate-200 bg-white text-slate-500'}`}>
                <div className="flex flex-col">
                  <span className="font-bold text-sm">Alta Eficiência</span>
                  <span className="text-[10px] opacity-70 leading-tight">Melhora o COP do sistema</span>
                </div>
                <input 
                  type="checkbox" checked={altaEficiencia} onChange={e=>setAltaEficiencia(e.target.checked)}
                  className="w-5 h-5 rounded accent-emerald-600"
                />
             </label>
          </div>

          <button 
            onClick={calcular} disabled={loading}
            className={`py-3.5 rounded-xl font-bold text-white shadow-lg transition-all ${
              loading ? 'bg-slate-300' : 'bg-gradient-to-br from-blue-600 to-indigo-700 hover:shadow-blue-200'
            }`}
          >
            {loading ? 'Dimensionando...' : 'CALCULAR TUBOS ➡️'}
          </button>
        </div>

        {erro && <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm border border-red-100 mb-6">{erro}</div>}

        {resultado && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-in zoom-in-95 duration-300">
             <div className="bg-blue-50 p-5 rounded-2xl border-2 border-blue-100 text-center">
                <span className="text-[10px] font-black text-blue-400 uppercase tracking-widest">Linha de Líquido</span>
                <div className="text-3xl font-black text-blue-900 mt-1">{resultado.diametro_liquido}</div>
                <p className="text-xs text-blue-600 mt-2 font-medium">Alta Pressão</p>
             </div>
             <div className="bg-teal-50 p-5 rounded-2xl border-2 border-teal-100 text-center">
                <span className="text-[10px] font-black text-teal-400 uppercase tracking-widest">Linha de Sucção</span>
                <div className="text-3xl font-black text-teal-900 mt-1">{resultado.diametro_succao}</div>
                <p className="text-xs text-teal-600 mt-2 font-medium">Com Isolamento Térmico</p>
             </div>
             
             <div className="md:col-span-2 bg-emerald-50 p-4 rounded-xl border border-emerald-100 text-emerald-700 text-sm font-bold flex items-center justify-center gap-2">
                <span>✅</span> Tubulação dimensionada e adicionada à lista de materiais!
             </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CalculadoraTubulacao;
