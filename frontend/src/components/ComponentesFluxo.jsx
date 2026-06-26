import React, { useState, useEffect } from 'react';
import api from '../api';


const CATEGORIAS_MANUAL = [
  'Válvula de Expansão Termostática',
  'Filtro Secador',
  'Válvula Solenoide',
  'Visor de Líquido',
];

const novaLinhaManual = () => ({ categoria: '', modelo: '', fabricante: '', conexao: '', capacidade: '', custo: '' });

const FLUIDOS_SUPORTADOS = ['R404A', 'R22'];

const ComponentesFluxo = ({ cargaAlvo, fluido, tempEvap, tempAmb: tempAmbProp = 35, aoFinalizar }) => {

  // ── Modo de seleção ───────────────────────────────────────────────────
  const [modo, setModo] = useState('automatico');

  // ── Modo Automático — componentes do banco ────────────────────────────
  const [componentes,  setComponentes]  = useState([]);
  const [loading,      setLoading]      = useState(false);
  const [erro,         setErro]         = useState('');
  const [selecionados, setSelecionados] = useState({});

  // ── Solenoide (cálculo por Kv) ────────────────────────────────────────
  const [solenoidResult,      setSolenoidResult]      = useState(null);
  const [solenoidSelecionado, setSolenoidSelecionado] = useState(true);

  // ── Filtro Secador + Visor de Líquido ─────────────────────────────────
  const [temTanqueLiquido,  setTemTanqueLiquido]  = useState(true);
  const [acessorioResult,   setAcessorioResult]   = useState(null);
  const [filtroSelecionado, setFiltroSelecionado] = useState(true);
  const [visorSelecionado,  setVisorSelecionado]  = useState(true);

  // ── Modo Engenharia ───────────────────────────────────────────────────
  const [linhasManuais, setLinhasManuais] = useState([novaLinhaManual()]);
  const [tempAmb, setTempAmb] = useState(tempAmbProp);
  const tempCond = tempAmb + 10;

  React.useEffect(() => { setTempAmb(tempAmbProp); }, [tempAmbProp]);

  const cargaKw        = (cargaAlvo / 860).toFixed(2);
  const fluidoSuportado = FLUIDOS_SUPORTADOS.some(f => fluido?.toUpperCase() === f);

  // ── Busca todos os dados em paralelo ─────────────────────────────────
  const executarBusca = (canceladoRef) => {
    if (!cargaAlvo || cargaAlvo <= 0) return;
    setLoading(true); setErro('');
    setSolenoidResult(null); setAcessorioResult(null);

    const tcCond = parseFloat(tempAmb) + 10;

    const promises = [
      api.post('/api/v1/componentes', { capacidade_kcalh: cargaAlvo, fluido, temp_evap: tempEvap }),
      fluidoSuportado
        ? api.post('/api/v1/solenoide/selecionar', {
            fluido, te_c: parseFloat(tempEvap), tc_c: tcCond, capacidade_kw: parseFloat(cargaKw),
          })
        : Promise.resolve(null),
      api.post('/api/v1/acessorios/selecionar', {
        fluido, capacidade_kcalh: cargaAlvo, tem_tanque_liquido: temTanqueLiquido,
      }),
    ];

    Promise.allSettled(promises).then(([resComp, resSol, resAce]) => {
      if (canceladoRef && canceladoRef.current) return;

      if (resComp.status === 'fulfilled') {
        setComponentes(resComp.value.data);
        const initial = {};
        resComp.value.data.forEach(c => { initial[c.categoria] = true; });
        setSelecionados(initial);
      } else {
        setErro('Erro ao buscar componentes de fluxo.');
      }

      if (resSol.status === 'fulfilled' && resSol.value) {
        setSolenoidResult(resSol.value.data);
        setSolenoidSelecionado(true);
      }

      if (resAce.status === 'fulfilled' && resAce.value) {
        setAcessorioResult(resAce.value.data);
        setFiltroSelecionado(true);
        setVisorSelecionado(true);
      }

      setLoading(false);
    });
  };

  useEffect(() => {
    const ref = { current: false };
    executarBusca(ref);
    return () => { ref.current = true; };
  }, [cargaAlvo, fluido, tempEvap]);

  // Re-busca filtro/visor quando o técnico muda o toggle de tanque de líquido
  useEffect(() => {
    if (!cargaAlvo || cargaAlvo <= 0) return;
    api.post('/api/v1/acessorios/selecionar', {
      fluido, capacidade_kcalh: cargaAlvo, tem_tanque_liquido: temTanqueLiquido,
    }).then(res => {
      setAcessorioResult(res.data);
      setFiltroSelecionado(true);
      setVisorSelecionado(true);
    }).catch(() => {});
  }, [temTanqueLiquido]);

  const buscarComponentes = () => executarBusca(null);

  // Separadores automáticos (banco)
  const separadorLiqAuto = componentes.find(c =>
    c.categoria?.toLowerCase().includes('separador de líquido') ||
    c.categoria?.toLowerCase().includes('separador de liquido')
  ) || null;
  const separadorOleoAuto = componentes.find(c =>
    c.categoria?.toLowerCase().includes('separador de óleo') ||
    c.categoria?.toLowerCase().includes('separador de oleo')
  ) || null;

  // ── Finalizar Automático ──────────────────────────────────────────────
  const finalizar = () => {
    const itens = componentes
      .filter(c => selecionados[c.categoria])
      .map(c => ({
        item: `${c.categoria} ${c.modelo}`,
        quantidade: 1, unidade: 'un',
        detalhe: `${c.fabricante} | ${c.conexao_entrada} | ${c.faixa_operacao}`,
        custo_unitario: c.custo, preco: c.custo,
      }));

    if (solenoidResult && solenoidSelecionado) {
      itens.push({
        item: `Válvula Solenoide ${solenoidResult.modelo}`,
        quantidade: 1, unidade: 'un',
        detalhe: `Danfoss | Kv ${solenoidResult.kv} m³/h | ${Math.round(solenoidResult.capacidade_valvula_kw * 860).toLocaleString('pt-BR')} kcal/h`,
        custo_unitario: 0, preco: 0,
      });
    }

    if (acessorioResult && filtroSelecionado) {
      const f = acessorioResult.filtro_secador;
      itens.push({
        item: `Filtro Secador ${f.modelo}`,
        quantidade: 1, unidade: 'un',
        detalhe: `${f.fabricante} | ${f.tipo} | ${f.conexao}`,
        custo_unitario: 0, preco: 0,
      });
    }

    if (acessorioResult && visorSelecionado) {
      const v = acessorioResult.visor_liquido;
      itens.push({
        item: `Visor de Líquido ${v.modelo}`,
        quantidade: 1, unidade: 'un',
        detalhe: `${v.fabricante} | ${v.conexao} | ${v.tipo}`,
        custo_unitario: 0, preco: 0,
      });
    }

    if (aoFinalizar) aoFinalizar(itens);
  };

  // ── Finalizar Engenharia ──────────────────────────────────────────────
  const finalizarEngenharia = () => {
    const itens = [];
    [separadorLiqAuto, separadorOleoAuto].filter(Boolean).forEach(sep => {
      itens.push({
        item: `${sep.categoria} ${sep.modelo}`,
        quantidade: 1, unidade: 'un',
        detalhe: `${sep.fabricante} | ${sep.conexao_entrada} | ${sep.faixa_operacao}`,
        custo_unitario: sep.custo, preco: sep.custo,
      });
    });
    linhasManuais
      .filter(l => l.modelo.trim() && l.categoria)
      .forEach(l => itens.push({
        item: `${l.categoria} ${l.modelo}`,
        quantidade: 1, unidade: 'un',
        detalhe: [l.fabricante, l.conexao, l.capacidade ? `${l.capacidade} kcal/h` : ''].filter(Boolean).join(' | '),
        custo_unitario: parseFloat(l.custo) || 0,
        preco: parseFloat(l.custo) || 0,
      }));
    if (aoFinalizar) aoFinalizar(itens);
  };

  const updateLinha = (i, campo, valor) => {
    const novas = [...linhasManuais];
    novas[i] = { ...novas[i], [campo]: valor };
    setLinhasManuais(novas);
  };

  const COOLSELECTOR_URL = `https://coolselectoronline.danfoss.com/`;

  const abrirCoolSelectorLadoALado = () => {
    const larguraTela = window.screen.width;
    const alturaTela  = window.screen.height;
    const metade      = Math.floor(larguraTela / 2);
    window.moveTo(0, 0);
    window.resizeTo(metade, alturaTela);
    window.open(COOLSELECTOR_URL, 'CoolSelector',
      `width=${metade},height=${alturaTela},left=${metade},top=0,resizable=yes,scrollbars=yes`);
  };

  // ── Card reutilizável para componentes automáticos ────────────────────
  const CardAuto = ({ selecionado, onToggle, categoria, badge, titulo, detalhe, nota, aviso, corBorda }) => {
    const cor = corBorda || 'emerald';
    const sels = {
      emerald: { borda: 'border-emerald-500 bg-emerald-50', check: 'bg-emerald-500 text-white', label: 'text-emerald-600' },
      purple:  { borda: 'border-purple-400 bg-purple-50',  check: 'bg-purple-500 text-white',  label: 'text-purple-600'  },
      cyan:    { borda: 'border-cyan-500 bg-cyan-50',       check: 'bg-cyan-500 text-white',    label: 'text-cyan-600'    },
      teal:    { borda: 'border-teal-500 bg-teal-50',       check: 'bg-teal-500 text-white',    label: 'text-teal-600'    },
    };
    const s = sels[cor] || sels.emerald;
    return (
      <div
        onClick={onToggle}
        className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex items-start gap-4 ${
          selecionado ? `${s.borda} shadow-sm` : 'border-slate-100 bg-white opacity-60 grayscale hover:grayscale-0 hover:opacity-100'
        }`}
      >
        <div className={`mt-1 w-5 h-5 rounded flex items-center justify-center text-[10px] font-black flex-shrink-0 ${
          selecionado ? s.check : 'bg-slate-200 text-slate-400'
        }`}>
          {selecionado ? '✓' : ''}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start gap-2">
            <span className={`text-[10px] font-black uppercase ${selecionado ? s.label : 'text-slate-400'}`}>
              {categoria}
            </span>
            {badge && (
              <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full flex-shrink-0 ${
                selecionado ? `${s.label} bg-white/60` : 'text-slate-400 bg-slate-100'
              }`}>
                {badge}
              </span>
            )}
          </div>
          <h4 className="font-bold text-slate-800">{titulo}</h4>
          <div className="text-[10px] text-slate-500 font-medium mt-1">{detalhe}</div>
          {nota && <div className={`text-[9px] font-bold mt-1 ${selecionado ? s.label : 'text-slate-400'}`}>{nota}</div>}
          {aviso && <div className="text-[9px] text-amber-600 bg-amber-50 rounded px-2 py-1 mt-1.5 border border-amber-200">{aviso}</div>}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
      <div className="bg-gradient-to-r from-[#7B2D8B] to-[#6BBF3F] px-6 py-4 flex justify-between items-center">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span className="bg-white/20 p-1.5 rounded-lg text-lg">🔧</span>
          Componentes de Fluxo e Segurança
        </h2>
        <div className="text-[10px] text-white/80 font-bold bg-white/20 px-3 py-1 rounded-full uppercase">
          {modo === 'automatico' ? 'Seleção Automática' : 'Modo Engenharia'}
        </div>
      </div>

      <div className="p-6">

        {/* ── Seletor de modo ── */}
        <div className="mb-6 bg-slate-50 rounded-xl border border-slate-200 p-1 flex gap-1">
          <button
            onClick={() => setModo('automatico')}
            className={`flex-1 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-2 ${
              modo === 'automatico'
                ? 'bg-[#7B2D8B] text-white shadow-md'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
            }`}
          >
            ⚡ Automático
            <span className={`text-[10px] font-normal ${modo === 'automatico' ? 'text-white/70' : 'text-slate-400'}`}>
              — banco de dados
            </span>
          </button>
          <button
            onClick={() => setModo('engenharia')}
            className={`flex-1 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-2 ${
              modo === 'engenharia'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
            }`}
          >
            🔬 Engenharia
            <span className={`text-[10px] font-normal ${modo === 'engenharia' ? 'text-white/70' : 'text-slate-400'}`}>
              — CoolSelector Danfoss
            </span>
          </button>
        </div>

        {/* ══ MODO AUTOMÁTICO ══ */}
        {modo === 'automatico' && (
          <>
            {/* Referência + toggle tanque de líquido */}
            <div className="mb-6 p-4 bg-slate-50 rounded-xl border border-slate-100">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-black text-slate-400 uppercase">Referência de Projeto</span>
                  <div className="text-sm font-bold text-slate-700">
                    {cargaAlvo?.toLocaleString('pt-BR')} kcal/h | {fluido} | {tempEvap}°C Evap.
                  </div>
                </div>
                <button onClick={buscarComponentes} className="text-xs font-bold text-emerald-600 hover:underline">
                  Recalcular
                </button>
              </div>

              {/* Toggle tanque de líquido */}
              <div className="mt-3 pt-3 border-t border-slate-200 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-slate-600">Sistema com tanque de líquido?</span>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    {temTanqueLiquido
                      ? 'Sim → Filtro secador DML (standalone)'
                      : 'Não → Filtro secador DMC (combinado com receptor)'}
                  </p>
                </div>
                <button
                  onClick={() => setTemTanqueLiquido(prev => !prev)}
                  className={`relative w-12 h-6 rounded-full transition-colors flex-shrink-0 ${
                    temTanqueLiquido ? 'bg-teal-500' : 'bg-slate-300'
                  }`}
                >
                  <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                    temTanqueLiquido ? 'translate-x-6' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>
            </div>

            {loading && <div className="p-8 text-center text-slate-500 animate-pulse">⚙️ Selecionando componentes...</div>}
            {erro    && <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-100 mb-4">{erro}</div>}

            {/* Grid de cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">

              {/* Componentes do banco (separadores) */}
              {componentes.map((comp, idx) => (
                <CardAuto
                  key={idx}
                  selecionado={!!selecionados[comp.categoria]}
                  onToggle={() => setSelecionados(prev => ({ ...prev, [comp.categoria]: !prev[comp.categoria] }))}
                  categoria={comp.categoria}
                  titulo={comp.modelo}
                  detalhe={`${comp.fabricante} | ${comp.conexao_entrada} | ${comp.faixa_operacao}`}
                  badge={`R$ ${comp.custo?.toLocaleString('pt-BR')}`}
                  corBorda="emerald"
                />
              ))}

              {/* Válvula Solenoide — cálculo por Kv */}
              {solenoidResult && (
                <CardAuto
                  selecionado={solenoidSelecionado}
                  onToggle={() => setSolenoidSelecionado(prev => !prev)}
                  categoria="Válvula Solenoide"
                  titulo={solenoidResult.modelo}
                  detalhe={`Danfoss | Kv ${solenoidResult.kv} m³/h | ${Math.round(solenoidResult.capacidade_valvula_kw * 860).toLocaleString('pt-BR')} kcal/h`}
                  nota={`⚡ Calculado por Kv — ${fluido} ${tempEvap}°C / T.Cond ${tempCond}°C`}
                  badge={`FS ${solenoidResult.fator_servico}×`}
                  corBorda="purple"
                />
              )}
              {!solenoidResult && !loading && !fluidoSuportado && (
                <div className="p-4 rounded-xl border-2 border-amber-200 bg-amber-50 flex items-start gap-4">
                  <div className="mt-1 w-5 h-5 rounded bg-amber-200 flex items-center justify-center text-[10px] font-black text-amber-600 flex-shrink-0">?</div>
                  <div>
                    <span className="text-[10px] font-black uppercase text-amber-600">Válvula Solenoide</span>
                    <p className="text-xs text-amber-700 mt-1">
                      Cálculo automático disponível para R404A e R22.{' '}
                      <button onClick={() => setModo('engenharia')} className="underline font-bold">Modo Engenharia</button> para CoolSelector.
                    </p>
                  </div>
                </div>
              )}

              {/* Filtro Secador — DML ou DMC */}
              {acessorioResult && (
                <CardAuto
                  selecionado={filtroSelecionado}
                  onToggle={() => setFiltroSelecionado(prev => !prev)}
                  categoria="Filtro Secador"
                  titulo={acessorioResult.filtro_secador.modelo}
                  detalhe={`Danfoss | ${acessorioResult.filtro_secador.tipo} | Linha ${acessorioResult.diametro_liquido}`}
                  nota={`🔵 ${acessorioResult.filtro_secador.motivo}`}
                  badge={acessorioResult.filtro_secador.tipo}
                  aviso={acessorioResult.filtro_secador.aviso}
                  corBorda="cyan"
                />
              )}

              {/* Visor de Líquido — SGN */}
              {acessorioResult && (
                <CardAuto
                  selecionado={visorSelecionado}
                  onToggle={() => setVisorSelecionado(prev => !prev)}
                  categoria="Visor de Líquido"
                  titulo={acessorioResult.visor_liquido.modelo}
                  detalhe={`Danfoss | ${acessorioResult.diametro_liquido} | ${acessorioResult.visor_liquido.tipo}`}
                  nota={`📍 ${acessorioResult.visor_liquido.posicao}`}
                  corBorda="teal"
                />
              )}

            </div>

            <button onClick={finalizar}
              className="w-full py-4 bg-[#7B2D8B] text-white rounded-xl font-bold hover:bg-purple-800 transition-all flex items-center justify-center gap-2 shadow-lg shadow-purple-200">
              CONFIRMAR ACESSÓRIOS E IR PARA TUBULAÇÃO ➡️
            </button>
          </>
        )}

        {/* ══ MODO ENGENHARIA ══ */}
        {modo === 'engenharia' && (
          <>
            <div className="mb-6 bg-blue-50 border-2 border-blue-200 rounded-xl p-5">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center text-white text-2xl flex-shrink-0">
                  🔬
                </div>
                <div className="flex-1">
                  <h3 className="font-black text-blue-900 text-base">CoolSelector®2 Online — Danfoss</h3>
                  <p className="text-sm text-blue-700 mt-1">
                    Acesse o seletor oficial da Danfoss para dimensionar todos os componentes com precisão de engenharia.
                    Após selecionar, registre os resultados abaixo.
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2 text-[10px] text-blue-600 font-bold">
                    <span>✓ VET • Filtro Secador • Solenoide • Visor</span>
                    <span>✓ R22 • R404A • R448A • CO₂</span>
                    <span>✓ Sep. Líquido + Sep. Óleo: automáticos</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 bg-white rounded-lg border border-blue-100 p-3">
                <p className="text-[10px] font-black text-blue-500 uppercase tracking-widest mb-2">
                  Parâmetros do projeto — use no CoolSelector:
                </p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-center mb-3">
                  <div className="bg-blue-50 rounded-lg px-2 py-2 border-2 border-blue-300 col-span-2 md:col-span-1">
                    <p className="text-[9px] text-blue-500 uppercase font-bold">Capacidade</p>
                    <p className="text-sm font-black text-blue-800">{cargaAlvo?.toLocaleString('pt-BR')} kcal/h</p>
                    <div className="mt-1 bg-orange-100 rounded px-2 py-0.5 border border-orange-300">
                      <p className="text-[10px] font-black text-orange-700">→ {cargaKw} kW</p>
                      <p className="text-[8px] text-orange-500 font-bold">⚠️ usar kW no CoolSelector</p>
                    </div>
                  </div>
                  <div className="bg-blue-50 rounded-lg px-2 py-2">
                    <p className="text-[9px] text-blue-400 uppercase font-bold">Fluido</p>
                    <p className="text-sm font-black text-blue-800">{fluido}</p>
                  </div>
                  <div className="bg-blue-50 rounded-lg px-2 py-2">
                    <p className="text-[9px] text-blue-400 uppercase font-bold">T. Evaporação</p>
                    <p className="text-sm font-black text-blue-800">{tempEvap}°C</p>
                  </div>
                  <div className="bg-emerald-50 rounded-lg px-2 py-2 border border-emerald-200">
                    <p className="text-[9px] text-emerald-500 uppercase font-bold">T. Condensação</p>
                    <p className="text-sm font-black text-emerald-800">{tempCond}°C</p>
                    <p className="text-[9px] text-emerald-400">T.Amb {tempAmb}°C+10</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 bg-slate-50 rounded-lg px-3 py-2 border border-slate-200">
                  <span className="text-[10px] text-slate-500 font-bold whitespace-nowrap">T. Ambiente:</span>
                  <input
                    type="number" value={tempAmb}
                    onChange={e => setTempAmb(parseInt(e.target.value) || 32)}
                    className="w-16 px-2 py-1 rounded border border-slate-300 text-center text-sm font-bold outline-none"
                  />
                  <span className="text-[10px] text-slate-400">°C → T.Cond = {tempAmb} + 10 = <strong>{tempCond}°C</strong></span>
                </div>
              </div>

              <div className="mt-3 bg-orange-50 border border-orange-300 rounded-lg px-4 py-2 flex items-center gap-3">
                <span className="text-orange-500 text-lg flex-shrink-0">⚠️</span>
                <p className="text-xs text-orange-700 font-medium">
                  <strong>Atenção:</strong> O CoolSelector usa <strong>kW</strong>.
                  Use <strong className="text-orange-800">{cargaKw} kW</strong> ao invés de {cargaAlvo?.toLocaleString('pt-BR')} kcal/h.
                </p>
              </div>

              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                <a href={COOLSELECTOR_URL} target="_blank" rel="noopener noreferrer"
                  className="py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2">
                  🔗 Abrir em nova aba
                </a>
                <button onClick={abrirCoolSelectorLadoALado}
                  className="py-3 bg-blue-700 hover:bg-blue-800 text-white rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-200">
                  ⬛⬛ Abrir lado a lado
                  <span className="text-[10px] text-blue-300 font-normal">— divide o monitor</span>
                </button>
              </div>

              <div className="mt-4 bg-amber-50 border border-amber-200 rounded-xl p-4">
                <p className="text-xs font-black text-amber-700 uppercase tracking-widest mb-3">
                  📖 Como selecionar no CoolSelector — passo a passo
                </p>
                <ol className="space-y-2">
                  {[
                    { n:1, txt: 'Aguarde carregar. Clique em "Language" → "Portuguese (Brazil)"' },
                    { n:2, txt: `Parâmetros: Fluido ${fluido} | T.Evap ${tempEvap}°C | T.Cond ${tempCond}°C | Cap. ${cargaKw} kW` },
                    { n:3, txt: 'VET: menu "Válvulas" → "VET" → calcular → anotar modelo' },
                    { n:4, txt: 'Filtro Secador: menu "Filtros" → Filtro Secador → anotar modelo' },
                    { n:5, txt: 'Válvula Solenoide: menu "Válvulas" → Solenoide → anotar modelo' },
                    { n:6, txt: 'Visor de Líquido: menu "Indicadores" → Visor → anotar modelo' },
                    { n:7, txt: 'Registre abaixo. Separadores de Líquido e Óleo já são automáticos.' },
                  ].map(p => (
                    <li key={p.n} className="flex gap-3 text-xs text-amber-800">
                      <span className="w-5 h-5 rounded-full bg-amber-400 text-white font-black flex items-center justify-center flex-shrink-0 text-[10px]">{p.n}</span>
                      <span>{p.txt}</span>
                    </li>
                  ))}
                </ol>
                <p className="mt-3 text-[10px] text-amber-500 italic">
                  ⚠️ O CoolSelector é um aplicativo remoto — campos não podem ser pré-preenchidos automaticamente.
                </p>
              </div>
            </div>

            {/* Separadores automáticos */}
            <div className="mb-6">
              <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">
                🔒 Separadores — seleção automática
              </h3>
              {loading && <div className="p-4 text-center text-slate-400 text-sm animate-pulse">Buscando separadores...</div>}
              {!loading && (
                <div className="space-y-2">
                  {[separadorLiqAuto, separadorOleoAuto].map((sep, idx) =>
                    sep ? (
                      <div key={idx} className="p-4 rounded-xl border-2 border-emerald-500 bg-emerald-50 flex items-start gap-4">
                        <div className="mt-1 w-5 h-5 rounded flex items-center justify-center text-[10px] font-black bg-emerald-500 text-white flex-shrink-0">✓</div>
                        <div className="flex-1">
                          <div className="flex justify-between items-start">
                            <span className="text-[10px] font-black uppercase text-emerald-600">{sep.categoria}</span>
                            <span className="text-xs font-bold text-slate-900">R$ {sep.custo?.toLocaleString('pt-BR')}</span>
                          </div>
                          <h4 className="font-bold text-slate-800">{sep.modelo}</h4>
                          <div className="text-[10px] text-slate-500 font-medium mt-1">
                            {sep.fabricante} | {sep.conexao_entrada} | {sep.faixa_operacao}
                          </div>
                          <div className="mt-1.5 inline-block bg-emerald-100 text-emerald-700 text-[9px] font-black px-2 py-0.5 rounded-full uppercase">
                            🔒 Selecionado automaticamente
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div key={idx} className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-700">
                        ⚠️ {idx === 0 ? 'Separador de Líquido' : 'Separador de Óleo'} não encontrado para esta faixa.
                      </div>
                    )
                  )}
                </div>
              )}
            </div>

            {/* Registro manual */}
            <div className="mb-6">
              <h3 className="text-sm font-black text-slate-700 mb-1">
                📋 Registrar componentes selecionados no CoolSelector
              </h3>
              <p className="text-[10px] text-slate-400 mb-4">
                VET, Filtro Secador, Válvula Solenoide e Visor de Líquido.
              </p>

              <div className="space-y-3">
                {linhasManuais.map((l, i) => (
                  <div key={i} className="bg-slate-50 rounded-xl border border-slate-200 p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-black text-slate-400 uppercase">Componente {i + 1}</span>
                      {linhasManuais.length > 1 && (
                        <button onClick={() => setLinhasManuais(linhasManuais.filter((_, j) => j !== i))}
                          className="text-red-400 hover:text-red-600 text-xs">✕ remover</button>
                      )}
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      <div className="col-span-2 md:col-span-1 space-y-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase">Categoria</label>
                        <select value={l.categoria} onChange={e => updateLinha(i, 'categoria', e.target.value)}
                          className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none bg-white">
                          <option value="">Selecione...</option>
                          {CATEGORIAS_MANUAL.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase">Modelo</label>
                        <input value={l.modelo} onChange={e => updateLinha(i, 'modelo', e.target.value)}
                          placeholder="Ex: T2 - 3"
                          className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase">Fabricante</label>
                        <input value={l.fabricante} onChange={e => updateLinha(i, 'fabricante', e.target.value)}
                          placeholder="Ex: Danfoss"
                          className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase">Conexão</label>
                        <input value={l.conexao} onChange={e => updateLinha(i, 'conexao', e.target.value)}
                          placeholder='Ex: 3/8"'
                          className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase">Capacidade (kcal/h)</label>
                        <input type="number" value={l.capacidade} onChange={e => updateLinha(i, 'capacidade', e.target.value)}
                          placeholder="Ex: 7178"
                          className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase">Custo (R$)</label>
                        <input type="number" value={l.custo} onChange={e => updateLinha(i, 'custo', e.target.value)}
                          placeholder="0,00"
                          className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm outline-none" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <button onClick={() => setLinhasManuais([...linhasManuais, novaLinhaManual()])}
                className="mt-3 text-sm font-bold text-blue-600 hover:underline flex items-center gap-1">
                + Adicionar componente
              </button>
            </div>

            <button
              onClick={finalizarEngenharia}
              disabled={!linhasManuais.some(l => l.modelo.trim()) && !separadorLiqAuto && !separadorOleoAuto}
              className="w-full py-4 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-200 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              CONFIRMAR COMPONENTES E IR PARA TUBULAÇÃO ➡️
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default ComponentesFluxo;
