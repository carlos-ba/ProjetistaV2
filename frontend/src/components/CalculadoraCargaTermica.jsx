import React, { useState, useEffect, useMemo } from 'react';
import api from '../api';
import PainelInsights from './PainelInsights';

const CalculadoraCargaTermica = ({ dadosIniciais, aoFinalizar, initialValues, onValoresChange, jaFinalizado = false, invalidado = false }) => {
  // --- VALIDAÇÃO: Verificar se gabinete foi configurado ---
  if (!dadosIniciais) {
    return (
      <div className="bg-yellow-50 border-2 border-yellow-400 rounded-xl p-8 text-center">
        <div className="text-5xl mb-4">⚠️</div>
        <h3 className="text-xl font-bold text-yellow-900 mb-2">Etapa Anterior Incompleta</h3>
        <p className="text-yellow-800 mb-4">
          Para calcular a carga térmica, você precisa primeiro configurar e confirmar o gabinete no <strong>Passo 1</strong>.
        </p>
        <p className="text-yellow-700 text-sm">
          Role para cima e preencha os dados do gabinete, depois clique em "Calcular e Confirmar Gabinete".
        </p>
      </div>
    );
  }

  // --- ESTADOS ---
  const [comprimento, setComprimento] = useState(5);
  const [largura, setLargura] = useState(4);
  const [altura, setAltura] = useState(3);
  const [tempExterna, setTempExterna] = useState(35);
  const [tempInterna, setTempInterna] = useState(-18);
  const [espessura, setEspessura] = useState(150);
  const [nucleo, setNucleo] = useState('PUR');
  const [tipoPiso, setTipoPiso] = useState('nenhum');

  const [produtos, setProdutos] = useState([]);
  const categorias = useMemo(
    () => [...new Set(produtos.map(p => p.tipo?.nome ?? p.tipo).filter(Boolean))].sort(),
    [produtos]
  );
  const [categoriaSelecionada, setCategoriaSelecionada] = useState(initialValues?.categoriaSelecionada ?? '');
  const [produtoSelecionado, setProdutoSelecionado] = useState(initialValues?.produtoSelecionado ?? '');
  const [movimentacao, setMovimentacao] = useState(initialValues?.movimentacao ?? 0);
  const [tempEntrada, setTempEntrada] = useState(initialValues?.tempEntrada ?? 5);
  const [tempoResfriamento, setTempoResfriamento] = useState(initialValues?.tempoResfriamento ?? 24);

  const [metodoInfiltracao, setMetodoInfiltracao] = useState(initialValues?.metodoInfiltracao ?? 'simplificado');
  const [urExterna, setUrExterna] = useState(initialValues?.urExterna ?? 60);
  const [urInterna, setUrInterna] = useState(initialValues?.urInterna ?? 90);

  const [iluminacao, setIluminacao] = useState(initialValues?.iluminacao ?? 0);
  const [pessoas, setPessoas] = useState(initialValues?.pessoas ?? 0);
  const [motor, setMotor] = useState(initialValues?.motor ?? 0);
  const [horasFuncionamento, setHorasFuncionamento] = useState(initialValues?.horasFuncionamento ?? 18);

  const [produtoDetalhe, setProdutoDetalhe] = useState(null);

  const [resultado, setResultado] = useState(initialValues?.resultado ?? null);
  const [erro, setErro] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusCalculo, setStatusCalculo] = useState((jaFinalizado || initialValues?.resultado) ? 'pronto' : null);

  useEffect(() => {
    if (onValoresChange) onValoresChange({ movimentacao, tempEntrada, tempoResfriamento, metodoInfiltracao, urExterna, urInterna, iluminacao, pessoas, motor, horasFuncionamento, categoriaSelecionada, produtoSelecionado, resultado });
  }, [movimentacao, tempEntrada, tempoResfriamento, metodoInfiltracao, urExterna, urInterna, iluminacao, pessoas, motor, horasFuncionamento, categoriaSelecionada, produtoSelecionado, resultado]);

  // Produtos filtrados com base na categoria
  const produtosFiltrados = categoriaSelecionada
    ? produtos.filter(p => (p.tipo?.nome ?? p.tipo) === categoriaSelecionada)
    : [];

  // Carregar produtos
  useEffect(() => {
    const carregarProdutos = async () => {
      try {
        const res = await api.get('/api/v1/catalogo/perfis-produto');
        const items = res.data?.results ?? res.data ?? [];
        setProdutos(items);
      } catch (e) {
        console.error("Erro ao carregar produtos:", e);
      }
    };
    carregarProdutos();
  }, []);

  // Sincronizar com Gabinete
  useEffect(() => {
    if (produtoSelecionado) {
      const p = produtos.find(item => item.id === parseInt(produtoSelecionado));
      setProdutoDetalhe(p);
    } else {
      setProdutoDetalhe(null);
    }
  }, [produtoSelecionado, produtos]);

  // Sincronizar com Gabinete
  // Monitorar mudanças para invalidar o cálculo (Sinalizador Amarelo)
  const carregandoDoArquivo = React.useRef(jaFinalizado);

  const primeirosDadosIniciais = React.useRef(true);
  useEffect(() => {
    if (dadosIniciais) {
      if (!primeirosDadosIniciais.current) {
        // Card 1 recalculou após o load inicial → libera detecção e invalida este card
        carregandoDoArquivo.current = false;
      }
      primeirosDadosIniciais.current = false;
      if (dadosIniciais.comprimento) setComprimento(dadosIniciais.comprimento);
      if (dadosIniciais.largura) setLargura(dadosIniciais.largura);
      if (dadosIniciais.altura) setAltura(dadosIniciais.altura);
      if (dadosIniciais.temperatura_interna !== undefined) setTempInterna(dadosIniciais.temperatura_interna);
      if (dadosIniciais.espessura) setEspessura(dadosIniciais.espessura);
      if (dadosIniciais.nucleo) setNucleo(dadosIniciais.nucleo);
      if (dadosIniciais.tipo_piso) setTipoPiso(dadosIniciais.tipo_piso);
    }
  }, [dadosIniciais]);
  const primeiroRender = React.useRef(true);
  useEffect(() => {
    if (primeiroRender.current) { primeiroRender.current = false; return; }
    if (carregandoDoArquivo.current) return;
    if (statusCalculo === 'pronto') {
      setStatusCalculo('modificado');
    }
  }, [
    comprimento, largura, altura, tempExterna, tempInterna, espessura, nucleo, tipoPiso,
    categoriaSelecionada, produtoSelecionado, movimentacao, tempEntrada, tempoResfriamento,
    iluminacao, pessoas, motor, horasFuncionamento
  ]);

  const calcular = async () => {
    setLoading(true);
    setErro('');
    const payload = {
      comprimento: parseFloat(comprimento) || 0,
      largura: parseFloat(largura) || 0,
      altura: parseFloat(altura) || 0,
      espessura_painel_mm: parseFloat(espessura) || 100,
      nucleo: nucleo || 'PUR',
      temp_externa: parseFloat(tempExterna) || 35,
      temp_interna: parseFloat(tempInterna) || 0,
      id_produto: produtoSelecionado ? parseInt(produtoSelecionado) : null,
      movimentacao_diaria_kg: parseFloat(movimentacao) || 0,
      temp_entrada_produto: parseFloat(tempEntrada) || 0,
      tempo_resfriamento_h: parseFloat(tempoResfriamento) || 24,
      potencia_iluminacao_w: parseFloat(iluminacao) || 0,
      horas_iluminacao_dia: 8,
      numero_pessoas: parseFloat(pessoas) || 0,
      horas_pessoas_dia: 4,
      potencia_outros_motores_w: parseFloat(motor) || 0,
      horas_outros_motores_dia: 18,
      tipo_piso: tipoPiso,
      calcular_infiltracao: true,
      metodo_infiltracao: metodoInfiltracao,
      ur_externa: parseFloat(urExterna) || 60,
      ur_interna: parseFloat(urInterna) || 90,
      fator_seguranca_perc: 10,
      horas_funcionamento_motor: parseFloat(horasFuncionamento) || 18
    };

    try {
      const response = await api.post('/api/v1/carga-termica', payload);
      setResultado(response.data);
      setStatusCalculo('pronto');
      if (aoFinalizar) aoFinalizar(response.data.capacidade_requerida_equipamento_kcalh, parseFloat(tempExterna));
    } catch (error) {
      console.error("Erro no cálculo:", error);
      setErro(error.response?.data?.erro || 'Erro ao calcular carga térmica.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden transition-all hover:shadow-xl">
      <div className="bg-gradient-to-r from-[#7B2D8B] to-[#6BBF3F] px-6 py-4 flex justify-between items-center">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span className="bg-white/20 p-1.5 rounded-lg text-lg">❄️</span>
          2. Cálculo de Carga Térmica
        </h2>

        {/* SINALIZADOR DE STATUS */}
        {statusCalculo && (
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] font-black uppercase transition-all shadow-lg ${
            statusCalculo === 'pronto' 
              ? 'bg-emerald-500 text-white animate-pulse' 
              : 'bg-yellow-400 text-yellow-900 border-2 border-yellow-500'
          }`}>
            <span className={`w-2 h-2 rounded-full ${statusCalculo === 'pronto' ? 'bg-white' : 'bg-yellow-900 animate-ping'}`}></span>
            {statusCalculo === 'pronto' ? 'Cálculo Pronto' : 'Dados Modificados'}
          </div>
        )}
      </div>

      <div className="p-6" onFocus={() => { carregandoDoArquivo.current = false; }} onInput={() => { carregandoDoArquivo.current = false; }}>

        {/* Banner dados do gabinete alterados */}
        {invalidado && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-300 rounded-xl flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="text-sm font-semibold text-amber-800">Dados do gabinete foram alterados</p>
              <p className="text-xs text-amber-600">Recalcule a carga térmica para atualizar o projeto</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Dimensões */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Dimensões (CxLxA)</label>
            <div className="flex gap-2">
              <input type="number" value={comprimento} onChange={e=>setComprimento(e.target.value)} className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none text-slate-900" placeholder="C" />
              <input type="number" value={largura} onChange={e=>setLargura(e.target.value)} className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none text-slate-900" placeholder="L" />
              <input type="number" value={altura} onChange={e=>setAltura(e.target.value)} className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none text-slate-900" placeholder="A" />
            </div>
          </div>

          {/* Temperaturas */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Temperaturas (°C)</label>
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <span className="absolute left-3 top-2.5 text-[10px] uppercase font-bold text-slate-400">Ext</span>
                <input type="number" value={tempExterna} onChange={e=>setTempExterna(e.target.value)} className="w-full pl-10 pr-3 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none text-slate-900" />
              </div>
              <div className="flex-1 relative">
                <span className="absolute left-3 top-2.5 text-[10px] uppercase font-bold text-blue-400">Int</span>
                <input type="number" value={tempInterna} onChange={e=>setTempInterna(e.target.value)} className="w-full pl-10 pr-3 py-2 rounded-lg border border-blue-200 bg-blue-50 text-blue-900 font-medium focus:ring-2 focus:ring-blue-500 outline-none" />
              </div>
            </div>
          </div>

          {/* Isolamento (Informativo vindo do Gabinete) */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Isolamento Base</label>
            <div className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-600">
              {espessura}mm / {nucleo} | Piso: {tipoPiso === 'painel' ? 'Painel' : tipoPiso === 'convencional' ? 'Isolado' : 'Sem Isol.'}
            </div>
          </div>
        </div>

        {/* Seção de Infiltração */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 mb-6">
          <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
            💨 Infiltração por Abertura de Portas
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Método de Cálculo</label>
              <select
                value={metodoInfiltracao}
                onChange={e => setMetodoInfiltracao(e.target.value)}
                className="w-full px-4 py-2 rounded-lg border border-slate-300 bg-white text-slate-900 focus:ring-2 focus:ring-emerald-500 outline-none"
              >
                <option value="simplificado">Simplificado (ASHRAE tabelado)</option>
                <option value="psicrometrico">Psicrométrico (por temperatura e UR)</option>
              </select>
              <p className="text-[10px] text-slate-400 mt-1">
                {metodoInfiltracao === 'simplificado'
                  ? 'Entalpias fixas: ext=85 kJ/kg / int=9 kJ/kg'
                  : 'Entalpias calculadas pela temperatura e umidade relativa reais'}
              </p>
            </div>

            {metodoInfiltracao === 'psicrometrico' && (
              <>
                <div>
                  <label className="text-xs font-bold text-slate-500 uppercase block mb-1">UR Externa (%)</label>
                  <div className="relative">
                    <input
                      type="number" min="0" max="100"
                      value={urExterna}
                      onChange={e => setUrExterna(e.target.value)}
                      className="w-full px-4 py-2 rounded-lg border border-orange-300 bg-orange-50 text-orange-900 font-medium focus:ring-2 focus:ring-orange-400 outline-none"
                    />
                    <span className="absolute right-3 top-2.5 text-[10px] text-orange-400 font-bold">%</span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">Umidade do ar externo (típico BR: 60–80%)</p>
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-500 uppercase block mb-1">UR Interna (%)</label>
                  <div className="relative">
                    <input
                      type="number" min="0" max="100"
                      value={urInterna}
                      onChange={e => setUrInterna(e.target.value)}
                      className="w-full px-4 py-2 rounded-lg border border-blue-300 bg-blue-50 text-blue-900 font-medium focus:ring-2 focus:ring-blue-400 outline-none"
                    />
                    <span className="absolute right-3 top-2.5 text-[10px] text-blue-400 font-bold">%</span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">Umidade interna da câmara (típico: 85–95%)</p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Seção de Produto */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 mb-8">
          <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
            📦 Produto e Movimentação
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-1">
              <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Categoria</label>
              <select
                value={categoriaSelecionada}
                onChange={e => {
                  setCategoriaSelecionada(e.target.value);
                  setProdutoSelecionado(''); // Reset produto ao mudar categoria
                }}
                className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none bg-white text-slate-900"
              >
                <option value="">Câmara Vazia (Somente Condução)</option>
                {categorias.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div className="md:col-span-1">
              <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Produto</label>
              <select
                value={produtoSelecionado}
                onChange={e => setProdutoSelecionado(e.target.value)}
                disabled={!categoriaSelecionada}
                className={`w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none bg-white text-slate-900 ${!categoriaSelecionada ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <option value="">Selecione o produto...</option>
                {produtosFiltrados.map(p => (
                  <option key={p.id} value={p.id}>{p.nome}</option>
                ))}
              </select>
            </div>

            {produtoSelecionado && (
              <>
                <div>
                  <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Movimentação (kg/dia)</label>
                  <input type="number" value={movimentacao} onChange={e=>setMovimentacao(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none bg-white text-slate-900" />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Temp. Entrada (°C)</label>
                  <input type="number" value={tempEntrada} onChange={e=>setTempEntrada(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none bg-white text-slate-900" />
                </div>
              </>
            )}
          </div>

          {produtoDetalhe && (
            <div className="mt-4 pt-4 border-t border-slate-200 grid grid-cols-2 md:grid-cols-4 gap-4">
               <div className="flex flex-col">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">T. Conservação</span>
                  <span className="text-sm font-bold text-slate-700">{produtoDetalhe.temperatura_conservacao !== null ? `${produtoDetalhe.temperatura_conservacao}°C` : 'N/A'}</span>
               </div>
               <div className="flex flex-col">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Umidade Relativa</span>
                  <span className="text-sm font-bold text-slate-700">{produtoDetalhe.umidade_relativa !== null ? `${produtoDetalhe.umidade_relativa}%` : 'N/A'}</span>
               </div>
               <div className="flex flex-col">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Teor de Água</span>
                  <span className="text-sm font-bold text-slate-700">{produtoDetalhe.teor_agua !== null ? `${produtoDetalhe.teor_agua}%` : 'N/A'}</span>
               </div>
               <div className="flex flex-col">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Pto. Congelamento</span>
                  <span className="text-sm font-bold text-slate-700">{produtoDetalhe.ponto_congelamento}°C</span>
               </div>
            </div>
          )}
        </div>

        {/* Cargas Internas e Configurações de Tempo */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block text-center">Pessoas</label>
            <div className="flex items-center justify-center gap-3 bg-white border border-slate-200 rounded-xl p-2">
               <button onClick={() => setPessoas(Math.max(0, pessoas - 1))} className="w-8 h-8 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-500">-</button>
               <span className="font-bold text-lg w-8 text-center">{pessoas}</span>
               <button onClick={() => setPessoas(pessoas + 1)} className="w-8 h-8 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-500">+</button>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Iluminação (W)</label>
            <input type="number" value={iluminacao} onChange={e=>setIluminacao(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none text-slate-900" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Outros Motores (W)</label>
            <input type="number" value={motor} onChange={e=>setMotor(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none text-slate-900" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Funcionamento (h/dia)</label>
            <div className="relative">
              <input 
                type="number" 
                value={horasFuncionamento} 
                onChange={e=>setHorasFuncionamento(e.target.value)} 
                min="1" max="24"
                className="w-full px-4 py-2 rounded-lg border border-blue-300 bg-blue-50 text-blue-900 font-bold focus:ring-2 focus:ring-blue-500 outline-none" 
              />
              <p className="text-[9px] text-blue-600 mt-1 font-bold italic">💡 Recomendado: 16h a 20h</p>
            </div>
          </div>
        </div>

        {/* Banner dados alterados upstream */}
        {invalidado && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-300 rounded-xl flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="text-sm font-semibold text-amber-800">Dados do gabinete foram alterados</p>
              <p className="text-xs text-amber-600">Recalcule a carga térmica para atualizar o projeto</p>
            </div>
          </div>
        )}

        {/* Banner projeto carregado */}
        {jaFinalizado && !resultado && statusCalculo === 'pronto' && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-xl flex items-center gap-3">
            <span className="text-2xl">✅</span>
            <div>
              <p className="text-sm font-semibold text-green-800">Carga térmica calculada — dados carregados do arquivo</p>
              <p className="text-xs text-green-600">Clique em "Recalcular" para atualizar os resultados detalhados</p>
            </div>
          </div>
        )}

        <button
          onClick={calcular}
          disabled={loading}
          className={`w-full py-4 rounded-xl font-bold text-lg shadow-md transition-all flex items-center justify-center gap-2 ${
            loading
              ? 'bg-slate-300 cursor-not-allowed'
              : statusCalculo === 'modificado'
                ? 'bg-amber-500 hover:bg-amber-600 text-white ring-4 ring-amber-100'
                : statusCalculo === 'pronto' && !resultado
                  ? 'bg-green-600 hover:bg-green-700 text-white hover:-translate-y-0.5'
                  : 'bg-[#7B2D8B] hover:bg-purple-800 text-white hover:-translate-y-0.5 active:translate-y-0'
          }`}
        >
          {loading ? (
            'Calculando...'
          ) : statusCalculo === 'modificado' ? (
            <>⚠️ ATUALIZAR CÁLCULO 🔄</>
          ) : statusCalculo === 'pronto' && !resultado ? (
            '🔄 Recalcular Carga Térmica'
          ) : (
            'CALCULAR CARGA E PROSSEGUIR ➡️'
          )}
        </button>

        {erro && <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm border border-red-200">{erro}</div>}

        {resultado && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="bg-emerald-50 p-6 rounded-2xl border border-emerald-100 flex flex-col justify-center items-center text-center">
              <span className="text-emerald-600 text-xs font-black uppercase tracking-widest mb-1">Capacidade Requerida</span>
              <div className="text-3xl font-black text-emerald-800">{resultado.capacidade_requerida_equipamento_kcalh} <small className="text-lg font-normal">kcal/h</small></div>
              <p className="text-emerald-600 text-xs mt-2 font-medium">✅ Valor enviado para seleção de equipamentos</p>
            </div>
            <div className="bg-white p-6 rounded-2xl border border-slate-200">
              <h4 className="text-sm font-bold text-slate-700 mb-3 uppercase tracking-tight">Composição Detalhada da Carga</h4>
              <ul className="space-y-2 text-sm">
                <li className="flex justify-between items-center text-slate-600">
                  <span>Condução Térmica:</span>
                  <span className="font-bold text-slate-900">{resultado.carga_conducao_kcalh} kcal/h</span>
                </li>
                {resultado.carga_infiltracao_kcalh > 0 && (
                  <li className="flex flex-col gap-0.5">
                    <div className="flex justify-between items-center text-slate-600">
                      <span>Infiltração por Portas:</span>
                      <span className="font-bold text-slate-900">{resultado.carga_infiltracao_kcalh} kcal/h</span>
                    </div>
                    {resultado.info_infiltracao && (
                      <p className="text-[10px] text-slate-400 italic pl-1">{resultado.info_infiltracao}</p>
                    )}
                  </li>
                )}
                <li className="flex justify-between items-center text-slate-600">
                  <span>Produto/Movimentação:</span>
                  <span className="font-bold text-slate-900">{resultado.carga_produto_kcalh} kcal/h</span>
                </li>
                {resultado.carga_respiracao_kcalh > 0 && (
                  <li className="flex justify-between items-center text-slate-600">
                    <span>Respiração do Produto:</span>
                    <span className="font-bold text-slate-900">{resultado.carga_respiracao_kcalh} kcal/h</span>
                  </li>
                )}
                
                {/* Detalhamento Interno */}
                <li className="flex justify-between items-center text-slate-400 pt-1 text-[11px] uppercase font-bold">
                  <span>Subtotal Cargas Internas:</span>
                  <span>{resultado.carga_internas_total_kcalh} kcal/h</span>
                </li>
                <li className="flex justify-between items-center text-slate-500 pl-4 border-l-2 border-slate-100">
                  <span>Iluminação:</span>
                  <span>{resultado.carga_iluminacao_kcalh} kcal/h</span>
                </li>
                <li className="flex justify-between items-center text-slate-500 pl-4 border-l-2 border-slate-100">
                  <span>Pessoas:</span>
                  <span>{resultado.carga_pessoas_kcalh} kcal/h</span>
                </li>
                <li className="flex justify-between items-center text-slate-500 pl-4 border-l-2 border-slate-100">
                  <span>Motores/Outros:</span>
                  <span>{resultado.carga_motores_kcalh} kcal/h</span>
                </li>

                <li className="flex justify-between items-center pt-2 mt-2 border-t border-slate-200 text-slate-800 font-bold">
                  <span>CARGA LÍQUIDA (24h):</span>
                  <span>{resultado.carga_total_24h_kcalh} kcal/h</span>
                </li>
                <li className="flex justify-between items-center text-emerald-600 text-xs italic">
                  <span>Fator de Segurança ({resultado.fator_seguranca_aplicado}):</span>
                  <span>+ {Math.round(resultado.carga_total_com_seguranca_kcalh - resultado.carga_total_24h_kcalh)} kcal/h</span>
                </li>

                <li className="flex justify-between items-center pt-2 mt-2 border-t border-slate-100 text-blue-600 font-bold">
                  <span>Tempo Compressor:</span>
                  <span>{resultado.baseado_em_horas_funcionamento}h/dia</span>
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CalculadoraCargaTermica;
