import React, { useState, useEffect } from 'react';
import api from '../api';

const SelecaoEquipamentos = ({ cargaInicial, tempInterna, onDeltaTChange, aoFinalizar }) => {
  const [cargaTotal, setCargaTotal] = useState(2000);
  const [numMaquinas, setNumMaquinas] = useState(1);
  const [deltaT, setDeltaT] = useState('');
  const [evap, setEvap] = useState('');
  const [cond, setCond] = useState(45);
  const [fluido, setFluido] = useState('R22');
  const [tipo, setTipo] = useState('Unidade Condensadora');

  const [resultados, setResultados] = useState([]);
  const [selecionados, setSelecionados] = useState([]); // Rascunho local
  const [quantidades, setQuantidades] = useState({}); // Controle de quantidade por modelo na busca
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState('');

  const cargaReferencia = Math.round(cargaTotal / numMaquinas);

  useEffect(() => {
    if (cargaInicial && cargaInicial > 0) {
      setCargaTotal(Math.round(cargaInicial));
    }
  }, [cargaInicial]);

  // Recalcula T. evaporação sempre que tempInterna ou deltaT mudar
  useEffect(() => {
    const tInt = parseFloat(tempInterna);
    const dt = parseFloat(deltaT);
    if (!isNaN(tInt) && !isNaN(dt)) {
      setEvap(tInt - dt);
    } else {
      setEvap('');
    }
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
    setResultados([]);
    setQuantidades({}); // Limpa quantidades ao buscar

    try {
      const response = await api.post('/api/v1/selecao', {
        carga_termica_total: cargaReferencia,
        temp_evaporacao: evapVal,
        temp_condensacao: cond,
        fluido: fluido,
        tipo: tipo
      });
      setResultados(response.data);
      
      // Inicializa quantidades com o número de máquinas definido pelo usuário para facilitar
      const initialQtys = {};
      response.data.forEach(item => {
        initialQtys[item.id] = numMaquinas;
      });
      setQuantidades(initialQtys);

      if (response.data.length === 0) setErro('Nenhum equipamento compatível encontrado.');
    } catch (error) {
      console.error(error);
      setErro('Erro de conexão com o servidor.');
    } finally {
      setLoading(false);
    }
  };

  const atualizarQuantidade = (id, valor) => {
    setQuantidades(prev => ({
      ...prev,
      [id]: Math.max(1, parseInt(valor) || 1)
    }));
  };

  const adicionarAoRascunho = (item) => {
    const qtd = quantidades[item.id] || 1;
    const novoItem = {
      nome: `${item.modelo} (${item.fabricante})`,
      preco: item.preco,
      qtde: qtd,
      detalhe: `${item.capacidade_real} kcal/h`,
      capacidade_real: item.capacidade_real,
      vazao_ar: item.vazao_ar, // Preserva a vazão para o painel lateral
      fluido: fluido,
      temp_evap: evap,
      modelo: item.modelo,
      id: item.id
    };
    setSelecionados([...selecionados, novoItem]);
    setResultados([]); // Limpa a busca para permitir nova seleção (ex: trocar de UC para Evap)
  };

  const removerDoRascunho = (idx) => {
    setSelecionados(selecionados.filter((_, i) => i !== idx));
  };

  const finalizarEtapa = () => {
    if (selecionados.length === 0) {
      alert("Selecione pelo menos um equipamento antes de avançar.");
      return;
    }
    if (aoFinalizar) {
      aoFinalizar(selecionados);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden transition-all hover:shadow-xl">
      <div className="bg-gradient-to-r from-[#7B2D8B] to-[#6BBF3F] px-6 py-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span className="bg-white/20 p-1.5 rounded-lg text-lg">⚙️</span>
          3. Seleção de Equipamentos
        </h2>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase">Carga Total (kcal/h)</label>
            <input 
              type="number" 
              value={cargaTotal} 
              onChange={e => setCargaTotal(e.target.value)} 
              className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all" 
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase">Nº Equipamentos</label>
            <input 
              type="number" 
              min="1"
              value={numMaquinas} 
              onChange={e => setNumMaquinas(Math.max(1, parseInt(e.target.value) || 1))} 
              className="w-full px-4 py-2 rounded-lg border border-blue-200 bg-blue-50 font-bold text-blue-700 focus:ring-2 focus:ring-blue-500 outline-none transition-all" 
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase">Ref. p/ Máquina</label>
            <div className="w-full px-4 py-2 rounded-lg border border-slate-200 bg-slate-50 font-black text-slate-700">
              {cargaReferencia} <small className="font-normal text-[9px]">kcal/h</small>
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase">Delta T (°C)</label>
            <input
              type="number" value={deltaT} onChange={e => setDeltaT(e.target.value)}
              placeholder="Ex: 6"
              className="w-full px-4 py-2 rounded-lg border border-blue-200 bg-blue-50 font-bold text-blue-700 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase">T. Evap (°C)</label>
            <input type="number" value={evap} onChange={e => setEvap(e.target.value)} placeholder="Calculada automaticamente" className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all" />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase">Fluido</label>
            <select value={fluido} onChange={e => setFluido(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none bg-white">
              <option value="R22">R22</option>
              <option value="R404A">R404A</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="md:col-span-1 space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase">Tipo de Equipamento</label>
            <select value={tipo} onChange={e => setTipo(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none bg-white">
              <option value="Unidade Condensadora">U. Condensadora</option>
              <option value="Evaporador">Evaporador</option>
            </select>
          </div>
        </div>

        <button 
          onClick={() => buscarEquipamentos()} 
          disabled={loading}
          className={`w-full py-3 rounded-lg font-bold shadow transition-all mb-8 ${
            loading ? 'bg-slate-300 cursor-not-allowed' : 'bg-[#7B2D8B] hover:bg-purple-800 text-white'
          }`}
        >
          {loading ? 'Buscando...' : '🔍 BUSCAR OPÇÕES NO CATÁLOGO'}
        </button>

        {erro && <div className="p-4 bg-amber-50 text-amber-700 border border-amber-200 rounded-lg text-sm mb-6">{erro}</div>}

        <div className="flex gap-6 overflow-x-auto pb-6 scrollbar-thin scrollbar-thumb-slate-200 scrollbar-track-transparent">
          {resultados.map((item, idx) => {
            // Lógica de cores baseada no status e na carga de referência
            // Verde (Ok): Diferença de +/- 10%
            // Âmbar (Menor): Abaixo de -10%
            // Azul (Maior): Acima de +10%
            
            const perc = (item.capacidade_real / cargaReferencia) * 100;
            let statusCor = 'ideal'; // Verde
            let label = '✅ Capacidade Ideal';

            if (perc < 90) {
              statusCor = 'menor'; // Âmbar
              label = '⚠️ Capacidade Menor';
            } else if (perc > 110) {
              statusCor = 'maior'; // Azul
              label = '🔵 Sobredimensionado';
            }

            const isSelecionado = selecionados.some(s => s.id === item.id || s.modelo === item.modelo);

            return (
              <div 
                key={idx} 
                className={`min-w-[280px] flex flex-col rounded-2xl border-2 transition-all p-5 ${
                  isSelecionado 
                    ? 'border-blue-500 bg-blue-50 ring-4 ring-blue-50 shadow-lg' 
                    : statusCor === 'ideal' 
                      ? 'border-emerald-200 bg-white hover:border-emerald-400' 
                      : statusCor === 'menor' 
                        ? 'border-amber-200 bg-white hover:border-amber-400' 
                        : 'border-blue-200 bg-white hover:border-blue-400'
                }`}
              >
                <div className="mb-4">
                  <span className={`text-[10px] font-black uppercase px-2 py-1 rounded-full ${
                    statusCor === 'ideal' ? 'bg-emerald-100 text-emerald-700' : statusCor === 'menor' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
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
                  
                  {/* Seletor de Quantidade */}
                  <div className="mt-4 pt-4 border-t border-slate-100">
                    <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Quantidade de Unidades</label>
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => atualizarQuantidade(item.id, (quantidades[item.id] || 1) - 1)}
                        className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold"
                      >
                        -
                      </button>
                      <input 
                        type="number" 
                        value={quantidades[item.id] || 1}
                        onChange={(e) => atualizarQuantidade(item.id, e.target.value)}
                        className="w-12 text-center font-bold text-slate-800 bg-transparent outline-none"
                      />
                      <button 
                        onClick={() => atualizarQuantidade(item.id, (quantidades[item.id] || 1) + 1)}
                        className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold"
                      >
                        +
                      </button>
                    </div>
                  </div>
                </div>

                <button 
                  onClick={() => adicionarAoRascunho(item)}
                  disabled={isSelecionado}
                  className={`mt-6 w-full py-3 rounded-xl font-bold transition-all border-2 ${
                    isSelecionado 
                      ? 'bg-blue-600 border-blue-600 text-white cursor-not-allowed' 
                      : 'border-slate-200 text-slate-600 hover:border-blue-500 hover:text-blue-500'
                  }`}
                >
                  {isSelecionado ? 'ADICIONADO ✓' : 'ADICIONAR 🛒'}
                </button>
              </div>
            );
          })}
        </div>

        {/* LISTA DE SELECIONADOS (RASCUNHO V2) */}
        {selecionados.length > 0 && (
          <div className="mt-8 border-t border-slate-100 pt-8 animate-in fade-in duration-500">
            <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
              <span className="text-blue-500">📋</span> Equipamentos Adicionados
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
                        <div className="font-bold text-slate-800">{s.nome}</div>
                        <div className="text-xs text-blue-600 font-bold">
                          {s.qtde} x R$ {s.preco.toLocaleString('pt-BR')} = R$ {(s.qtde * s.preco).toLocaleString('pt-BR')}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-500 text-sm">
                        {s.detalhe} {s.qtde > 1 && `(Total: ${s.qtde * s.capacidade_real} kcal/h)`}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button 
                          onClick={() => removerDoRascunho(idx)}
                          className="text-red-500 hover:text-red-700 p-2 hover:bg-red-50 rounded-lg transition-all"
                        >
                          🗑️
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button 
              onClick={finalizarEtapa}
              className="w-full py-4 bg-[#7B2D8B] hover:bg-purple-800 text-white font-black rounded-xl shadow-lg shadow-purple-200 transition-all hover:-translate-y-1 active:translate-y-0"
            >
              FINALIZAR SELEÇÃO E CONTINUAR ➡️
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SelecaoEquipamentos;
