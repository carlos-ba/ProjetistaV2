import React, { useState, useEffect } from 'react';
import api from '../api';

const CATEGORIAS_MANUAL = [
  'Válvula de Expansão Termostática',
  'Filtro Secador',
  'Válvula Solenoide',
  'Visor de Líquido',
];

const novaLinhaManual = () => ({ categoria: '', modelo: '', fabricante: '', conexao: '', capacidade: '', custo: '' });

// Categoria (texto) → tipo_item (slug estável usado na classificação do orçamento)
const slugPorCategoria = (cat = '') => {
  const c = cat.toLowerCase();
  if (c.includes('separador') && (c.includes('líquido') || c.includes('liquido'))) return 'separador_liquido';
  if (c.includes('separador') && (c.includes('óleo')   || c.includes('oleo')))    return 'separador_oleo';
  if (c.includes('expansão') || c.includes('expansao') || c.includes('vet'))       return 'valvula_expansao';
  if (c.includes('solenoide'))                                                      return 'valvula_solenoide';
  if (c.includes('filtro'))                                                         return 'filtro_secador';
  if (c.includes('visor'))                                                          return 'visor_liquido';
  return null;
};

const FLUIDOS_SUPORTADOS = ['R404A', 'R22'];

const ComponentesFluxo = ({ cargaAlvo, fluido, tempEvap, tempAmb: tempAmbProp = 35, evaporador, condensadora, dadosTubulacao, configuracoesMontagem, aoFinalizar, onCavaleteChange, initialValues, onValoresChange, jaFinalizado = false, invalidado = false, numCircuitos = 1 }) => {

  // Cada circuito é uma cópia da mesma UC → todo componente de fluxo é 1 por circuito.
  // Escala as quantidades pelo número de circuitos antes de enviar ao orçamento.
  const escalarPorCircuitos = (itens) => {
    const n = Math.max(1, parseInt(numCircuitos) || 1);
    if (n === 1) return itens;
    return itens.map(it => ({
      ...it,
      quantidade: +((it.quantidade || 0) * n).toFixed(3),
      detalhe: it.detalhe ? `${it.detalhe} | ×${n} circuitos` : `×${n} circuitos`,
    }));
  };

  // ── Modo de seleção ───────────────────────────────────────────────────
  const [modo, setModo] = useState(initialValues?.modo ?? 'automatico');

  // ── Modo Automático — componentes do banco ────────────────────────────
  const [componentes,  setComponentes]  = useState([]);
  const [loading,      setLoading]      = useState(false);
  const [erro,         setErro]         = useState('');
  const [selecionados, setSelecionados] = useState({});

  // ── Solenoide (cálculo por Kv) ────────────────────────────────────────
  const [solenoidResult,      setSolenoidResult]      = useState(null);
  const [solenoidSelecionado, setSolenoidSelecionado] = useState(initialValues?.solenoidSelecionado ?? true);

  // ── Filtro Secador + Visor de Líquido ─────────────────────────────────
  const cfg = configuracoesMontagem || {};
  const [temTanqueLiquido,  setTemTanqueLiquido]  = useState(initialValues?.temTanqueLiquido ?? true);
  const [acessorioResult,   setAcessorioResult]   = useState(null);
  const [filtroSelecionado, setFiltroSelecionado] = useState(initialValues?.filtroSelecionado ?? (cfg.incluir_filtro !== false));
  const [visorSelecionado,  setVisorSelecionado]  = useState(initialValues?.visorSelecionado  ?? (cfg.incluir_visor  !== false));

  // ── GBC Entrada/Saída ─────────────────────────────────────────────────
  const [gbcEntradaSelecionado, setGbcEntradaSelecionado] = useState(initialValues?.gbcEntradaSelecionado ?? (cfg.incluir_gbc_entrada !== false));
  const [gbcSaidaSelecionado,   setGbcSaidaSelecionado]   = useState(initialValues?.gbcSaidaSelecionado   ?? (cfg.incluir_gbc_saida   !== false));

  // ── Estimativa de carga de fluido ─────────────────────────────────────
  const [cargaFluido,        setCargaFluido]        = useState(null);
  const [comprimentoLiquido, setComprimentoLiquido] = useState(initialValues?.comprimentoLiquido ?? '');
  const [comprimentoSuccao,  setComprimentoSuccao]  = useState(initialValues?.comprimentoSuccao  ?? '');

  // ── Tanque de líquido ─────────────────────────────────────────────────
  const [tanqueResult,      setTanqueResult]      = useState(null);
  const [tanqueSelecionado, setTanqueSelecionado] = useState(initialValues?.tanqueSelecionado ?? true);

  // ── Cavalete de componentes ───────────────────────────────────────────
  const [cavaleteResult,      setCavaleteResult]      = useState(null);
  const [cavaleteIncluido,    setCavaleteIncluido]    = useState(initialValues?.cavaleteIncluido ?? true);

  // ── Modo Engenharia ───────────────────────────────────────────────────
  const [linhasManuais, setLinhasManuais] = useState(initialValues?.linhasManuais ?? [novaLinhaManual()]);
  const [tempAmb, setTempAmb] = useState(tempAmbProp);

  // Captura se havia dados salvos NO MOMENTO DO MOUNT (não após auto-sync via onValoresChange)
  const projetoSalvoNoMount = React.useRef(!!initialValues);

  useEffect(() => {
    if (onValoresChange) onValoresChange({ modo, solenoidSelecionado, temTanqueLiquido, filtroSelecionado, visorSelecionado, gbcEntradaSelecionado, gbcSaidaSelecionado, comprimentoLiquido, comprimentoSuccao, tanqueSelecionado, cavaleteIncluido, linhasManuais });
  }, [modo, solenoidSelecionado, temTanqueLiquido, filtroSelecionado, visorSelecionado, gbcEntradaSelecionado, gbcSaidaSelecionado, comprimentoLiquido, comprimentoSuccao, tanqueSelecionado, cavaleteIncluido, linhasManuais]);
  const tempCond = tempAmb + 10;

  React.useEffect(() => { setTempAmb(tempAmbProp); }, [tempAmbProp]);

  // Notifica App.jsx sempre que o resultado do cavalete ou tanque muda
  React.useEffect(() => {
    if (onCavaleteChange) onCavaleteChange(cavaleteResult, tanqueSelecionado && !!tanqueResult);
  }, [cavaleteResult, tanqueSelecionado, tanqueResult]);

  const cargaKw        = (cargaAlvo / 860).toFixed(2);
  const fluidoSuportado = FLUIDOS_SUPORTADOS.some(f => fluido?.toUpperCase() === f);

  // ── Busca todos os dados em paralelo ─────────────────────────────────
  const executarBusca = (canceladoRef) => {
    if (!cargaAlvo || cargaAlvo <= 0) return;
    const cfgAtual = configuracoesMontagem || {}; // captura no momento da chamada (já garantido não-null pelo useEffect)
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
        if (!projetoSalvoNoMount.current) {
          setFiltroSelecionado(cfgAtual.incluir_filtro !== false);
          setVisorSelecionado(cfgAtual.incluir_visor  !== false);
        }
      }

      setLoading(false);
    });
  };

  // Aguarda configuracoesMontagem antes de iniciar — aplica flags do perfil logo de início
  useEffect(() => {
    if (!configuracoesMontagem) return; // espera o perfil carregar
    const ref = { current: false };
    if (!projetoSalvoNoMount.current) {
      setFiltroSelecionado(configuracoesMontagem.incluir_filtro !== false);
      setVisorSelecionado(configuracoesMontagem.incluir_visor   !== false);
      setGbcEntradaSelecionado(configuracoesMontagem.incluir_gbc_entrada !== false);
      setGbcSaidaSelecionado(configuracoesMontagem.incluir_gbc_saida     !== false);
    }
    executarBusca(ref);
    return () => { ref.current = true; };
  }, [cargaAlvo, fluido, tempEvap, configuracoesMontagem]); // eslint-disable-line react-hooks/exhaustive-deps

  // Re-busca filtro/visor quando o técnico muda o toggle de tanque de líquido
  useEffect(() => {
    if (!cargaAlvo || cargaAlvo <= 0) return;
    api.post('/api/v1/acessorios/selecionar', {
      fluido, capacidade_kcalh: cargaAlvo, tem_tanque_liquido: temTanqueLiquido,
    }).then(res => {
      setAcessorioResult(res.data);
      // Não reseta filtro/visor — mantém o estado atual (escolha do usuário ou do perfil)
    }).catch(() => {});
  }, [temTanqueLiquido]);

  const buscarComponentes = () => executarBusca(null);

  // ── Estimar carga de fluido quando temos tubulação + comprimentos ──────
  const estimarCargaFluido = () => {
    if (!dadosTubulacao || !comprimentoLiquido || !comprimentoSuccao) return;
    const lm = parseFloat(comprimentoLiquido);
    const sm = parseFloat(comprimentoSuccao);
    if (isNaN(lm) || isNaN(sm) || lm <= 0 || sm <= 0) return;

    api.post('/api/v1/carga-fluido/estimar', {
      fluido,
      volume_interno_evap_kg: evaporador?.volume_interno_kg ?? null,
      volume_interno_uc_kg:   condensadora?.volume_interno_kg ?? null,
      bitola_liquido:         dadosTubulacao.diametro_liquido,
      comprimento_liquido_m:  lm,
      bitola_succao:          dadosTubulacao.diametro_succao,
      comprimento_succao_m:   sm,
    }).then(res => {
      setCargaFluido(res.data);
      // Seleciona tanque de líquido automaticamente com base na carga calculada
      return api.post('/api/v1/tanque-liquido/selecionar', {
        fluido,
        carga_total_kg: res.data.carga_total_kg,
      });
    }).then(res => {
      setTanqueResult(res.data);
      setTanqueSelecionado(true);
      // Encadeia análise do cavalete
      analisarCavaleteAuto(res.data);
    }).catch(() => {});
  };

  const analisarCavaleteAuto = (tanque) => {
    if (!dadosTubulacao || !configuracoesMontagem) return;
    if (!condensadora?.conexao_liquido || !evaporador?.conexao_liquido) return;
    if (!acessorioResult) return;

    const lm = parseFloat(comprimentoLiquido) || 0;
    const sm = parseFloat(comprimentoSuccao)  || 0;
    const cfg = configuracoesMontagem;

    api.post('/api/v1/cavalete/analisar', {
      condensadora_cx_liquido: condensadora.conexao_liquido,
      condensadora_cx_succao:  condensadora.conexao_succao,
      evaporador_cx_liquido:   evaporador.conexao_liquido,
      evaporador_cx_succao:    evaporador.conexao_succao,
      diametro_liquido:        dadosTubulacao.diametro_liquido,
      diametro_succao:         dadosTubulacao.diametro_succao,
      filtro_conexao:          acessorioResult.filtro_secador.conexao,
      filtro_tipo:             cfg.tipo_filtro,
      solenoide_conexao:       solenoidResult?.conexao || dadosTubulacao.diametro_liquido,
      visor_conexao:           acessorioResult.visor_liquido.conexao,
      visor_tipo:              cfg.tipo_visor,
      vet_entrada:             '3/8"',
      vet_saida:               '1/2"',
      comprimento_liquido_m:   lm,
      comprimento_succao_m:    sm,
      trecho_vet_evap_m:       cfg.trecho_vet_evap,
      trecho_evap_sifao_m:     cfg.trecho_evap_sifao,
      trecho_subida_m:         cfg.trecho_subida,
      trecho_sifao_gbc_m:      cfg.trecho_sifao_gbc,
      tanque_conexao:          tanque?.tanque?.conexao ?? null,
      incluir_filtro:          filtroSelecionado,
      incluir_visor:           visorSelecionado,
      incluir_gbc_entrada:     gbcEntradaSelecionado,
      incluir_gbc_saida:       gbcSaidaSelecionado,
    }).then(res => {
      setCavaleteResult(res.data);
      setCavaleteIncluido(true);
    }).catch(() => {});
  };

  // Auto-gera cavalete ao carregar projeto do arquivo
  // Aguarda acessorioResult (vindo da API automática) e então dispara a cadeia completa
  const jaFinalizadoRef = React.useRef(jaFinalizado);
  useEffect(() => {
    if (!jaFinalizadoRef.current) return;
    if (!acessorioResult) return;
    if (!dadosTubulacao || !comprimentoLiquido || !comprimentoSuccao) return;
    jaFinalizadoRef.current = false; // executa só uma vez
    estimarCargaFluido();
  }, [acessorioResult]); // eslint-disable-line react-hooks/exhaustive-deps

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
        tipo_item: slugPorCategoria(c.categoria),
        quantidade: 1, unidade: 'un',
        detalhe: `${c.fabricante} | ${c.conexao_entrada} | ${c.faixa_operacao}`,
        custo_unitario: c.custo, preco: c.custo,
      }));

    if (solenoidResult && solenoidSelecionado) {
      itens.push({
        item: `Válvula Solenoide ${solenoidResult.modelo}`,
        tipo_item: 'valvula_solenoide',
        quantidade: 1, unidade: 'un',
        detalhe: `Danfoss | Kv ${solenoidResult.kv} m³/h | ${Math.round(solenoidResult.capacidade_valvula_kw * 860).toLocaleString('pt-BR')} kcal/h`,
        custo_unitario: 0, preco: 0,
      });
    }

    if (acessorioResult && filtroSelecionado) {
      const f = acessorioResult.filtro_secador;
      itens.push({
        item: `Filtro Secador ${f.modelo}`,
        tipo_item: 'filtro_secador',
        quantidade: 1, unidade: 'un',
        detalhe: `${f.fabricante} | ${f.tipo} | ${f.conexao}`,
        custo_unitario: 0, preco: 0,
      });
    }

    if (acessorioResult && visorSelecionado) {
      const v = acessorioResult.visor_liquido;
      itens.push({
        item: `Visor de Líquido ${v.modelo}`,
        tipo_item: 'visor_liquido',
        quantidade: 1, unidade: 'un',
        detalhe: `${v.fabricante} | ${v.conexao} | ${v.tipo}`,
        custo_unitario: 0, preco: 0,
      });
    }

    if (tanqueResult && tanqueSelecionado) {
      const t = tanqueResult.tanque;
      itens.push({
        item: `Tanque de Líquido ${t.fabricante} ${t.modelo}`,
        tipo_item: 'tanque_liquido',
        quantidade: 1, unidade: 'un',
        detalhe: `Vol. total ${t.volume_total_l} L | Vol. útil ${t.volume_util_l} L (NBR 16.069) | ${t.conexao}`,
        custo_unitario: 0, preco: 0,
      });
    }

    if (cavaleteResult && cavaleteIncluido) {
      cavaleteResult.resumo.forEach(it => {
        itens.push({
          item: it.item,
          tipo_item: it.tipo_item,
          quantidade: it.quantidade,
          unidade: it.unidade,
          detalhe: it.detalhe || 'Cavalete de montagem',
          custo_unitario: 0, preco: 0,
        });
      });
    }

    if (cargaFluido) {
      const fluido = evaporador?.fluido || condensadora?.fluido || 'Fluido';
      itens.push({
        item: `Carga de Fluido ${fluido}`,
        tipo_item: 'carga_fluido',
        quantidade: cargaFluido.carga_total_kg,
        unidade: 'kg',
        detalhe: `Evaporador ${cargaFluido.carga_evaporador_kg} kg | UC ${cargaFluido.carga_uc_kg} kg | Linha líquido ${cargaFluido.carga_linha_liquido_kg} kg | Linha sucção ${cargaFluido.carga_linha_succao_kg} kg`,
        aviso: cargaFluido.aviso_volume_uc || null,
        custo_unitario: 0, preco: 0,
      });
    }

    if (aoFinalizar) aoFinalizar(escalarPorCircuitos(itens));
  };

  // ── Finalizar Engenharia ──────────────────────────────────────────────
  const finalizarEngenharia = () => {
    const itens = [];
    [separadorLiqAuto, separadorOleoAuto].filter(Boolean).forEach(sep => {
      itens.push({
        item: `${sep.categoria} ${sep.modelo}`,
        tipo_item: slugPorCategoria(sep.categoria),
        quantidade: 1, unidade: 'un',
        detalhe: `${sep.fabricante} | ${sep.conexao_entrada} | ${sep.faixa_operacao}`,
        custo_unitario: sep.custo, preco: sep.custo,
      });
    });
    linhasManuais
      .filter(l => l.modelo.trim() && l.categoria)
      .forEach(l => itens.push({
        item: `${l.categoria} ${l.modelo}`,
        tipo_item: slugPorCategoria(l.categoria),
        quantidade: 1, unidade: 'un',
        detalhe: [l.fabricante, l.conexao, l.capacidade ? `${l.capacidade} kcal/h` : ''].filter(Boolean).join(' | '),
        custo_unitario: parseFloat(l.custo) || 0,
        preco: parseFloat(l.custo) || 0,
      }));
    if (aoFinalizar) aoFinalizar(escalarPorCircuitos(itens));
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

        {(parseInt(numCircuitos) || 1) > 1 && (
          <div className="mb-6 px-4 py-2.5 bg-indigo-50 border border-indigo-200 rounded-lg text-xs text-indigo-800 font-semibold">
            🔁 {numCircuitos} circuitos — cada componente é 1 por circuito. As quantidades enviadas ao orçamento
            são multiplicadas por {numCircuitos} automaticamente (os cards abaixo mostram o valor por circuito).
          </div>
        )}

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
                  className={`relative w-11 h-6 rounded-full transition-colors flex-shrink-0 ${
                    temTanqueLiquido ? 'bg-teal-500' : 'bg-slate-300'
                  }`}
                >
                  <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                    temTanqueLiquido ? 'translate-x-5' : 'translate-x-0'
                  }`} />
                </button>
              </div>

              {/* Toggles GBC Entrada / Saída */}
              <div className="mt-2 pt-2 border-t border-slate-200 grid grid-cols-2 gap-2">
                {[
                  { label: 'GBC Entrada', valor: gbcEntradaSelecionado, set: setGbcEntradaSelecionado },
                  { label: 'GBC Saída',   valor: gbcSaidaSelecionado,   set: setGbcSaidaSelecionado   },
                ].map(({ label, valor, set }) => (
                  <div key={label} className="flex items-center justify-between gap-2 bg-slate-100 rounded-lg px-3 py-2">
                    <span className="text-xs font-bold text-slate-600">{label}</span>
                    <button
                      onClick={() => set(prev => !prev)}
                      className={`relative w-9 h-5 rounded-full transition-colors flex-shrink-0 ${
                        valor ? 'bg-violet-500' : 'bg-slate-300'
                      }`}
                    >
                      <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                        valor ? 'translate-x-4' : 'translate-x-0'
                      }`} />
                    </button>
                  </div>
                ))}
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

            {/* ── Estimativa de Carga de Fluido ── */}
            {dadosTubulacao && (
              <div className="mb-6 bg-indigo-50 border-2 border-indigo-200 rounded-xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <span className="text-[10px] font-black text-indigo-500 uppercase tracking-widest">Estimativa de Carga de Fluido</span>
                    <p className="text-xs text-indigo-700 mt-0.5">
                      Bitolas: líquido <strong>{dadosTubulacao.diametro_liquido}</strong> | sucção <strong>{dadosTubulacao.diametro_succao}</strong>
                      {evaporador?.volume_interno_kg ? ` | evap. ${evaporador.volume_interno_kg} kg` : ' | volume evap. não disponível'}
                    </p>
                  </div>
                  {cargaFluido && (
                    <div className="text-right">
                      <div className="text-2xl font-black text-indigo-700">{cargaFluido.carga_total_kg} kg</div>
                      <div className="text-[10px] text-indigo-400 font-bold">CARGA TOTAL</div>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div>
                    <label className="text-[10px] font-bold text-indigo-500 uppercase">Comprimento linha líquido (m)</label>
                    <input
                      type="number" value={comprimentoLiquido}
                      onChange={e => setComprimentoLiquido(e.target.value)}
                      placeholder={dadosTubulacao.distancia_considerada?.toFixed(0) || '5'}
                      className="w-full mt-1 px-3 py-2 rounded-lg border border-indigo-200 text-sm outline-none bg-white"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-indigo-500 uppercase">Comprimento linha sucção (m)</label>
                    <input
                      type="number" value={comprimentoSuccao}
                      onChange={e => setComprimentoSuccao(e.target.value)}
                      placeholder={dadosTubulacao.distancia_considerada?.toFixed(0) || '5'}
                      className="w-full mt-1 px-3 py-2 rounded-lg border border-indigo-200 text-sm outline-none bg-white"
                    />
                  </div>
                </div>

                <button
                  onClick={estimarCargaFluido}
                  disabled={!comprimentoLiquido || !comprimentoSuccao}
                  className="w-full py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-700 transition-all disabled:opacity-40"
                >
                  Calcular Carga de Fluido
                </button>

                {cargaFluido && (
                  <div className="mt-3 grid grid-cols-4 gap-2 text-center">
                    {[
                      { label: 'Evaporador', valor: cargaFluido.carga_evaporador_kg },
                      { label: 'UC', valor: cargaFluido.carga_uc_kg },
                      { label: 'Linha Líquido', valor: cargaFluido.carga_linha_liquido_kg },
                      { label: 'Linha Sucção', valor: cargaFluido.carga_linha_succao_kg },
                    ].map(item => (
                      <div key={item.label} className="bg-white rounded-lg p-2 border border-indigo-100">
                        <div className="text-xs font-black text-indigo-700">{item.valor} kg</div>
                        <div className="text-[9px] text-indigo-400 font-bold uppercase">{item.label}</div>
                      </div>
                    ))}
                  </div>
                )}
                {cargaFluido?.nota && (
                  <p className="mt-2 text-[10px] text-amber-600 bg-amber-50 rounded px-2 py-1 border border-amber-200">{cargaFluido.nota}</p>
                )}
                {cargaFluido?.aviso_volume_uc && (
                  <p className="mt-2 text-[10px] text-red-600 bg-red-50 rounded px-2 py-1 border border-red-200">⚠ {cargaFluido.aviso_volume_uc}</p>
                )}
              </div>
            )}

            {/* ── Tanque de Líquido ── */}
            {tanqueResult && (
              <CardAuto
                selecionado={tanqueSelecionado}
                onToggle={() => setTanqueSelecionado(prev => !prev)}
                categoria="Tanque de Líquido"
                titulo={`${tanqueResult.tanque.fabricante} ${tanqueResult.tanque.modelo}`}
                detalhe={`Vol. total ${tanqueResult.tanque.volume_total_l} L | Vol. útil ${tanqueResult.tanque.volume_util_l} L | Conexão ${tanqueResult.tanque.conexao}`}
                nota={`🔵 NBR 16.069 — vol. necessário ${tanqueResult.volume_necessario_l} L | carga ${tanqueResult.carga_total_kg} kg`}
                badge={tanqueResult.tanque.fabricante}
                aviso={tanqueResult.aviso}
                corBorda="violet"
              />
            )}

            {/* ── Cavalete de Componentes ── */}
            {cavaleteResult && (
              <div className="border-2 border-orange-300 rounded-xl overflow-hidden">
                <div className="bg-orange-50 px-4 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-base">🔧</span>
                    <div>
                      <p className="text-xs font-black text-orange-800 uppercase tracking-wide">Cavalete — Conexões e Reduções</p>
                      <p className="text-[10px] text-orange-500">{cavaleteResult.resumo.length} itens identificados</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setCavaleteIncluido(prev => !prev)}
                    className={`text-[10px] font-bold px-3 py-1 rounded-full border transition-all ${cavaleteIncluido ? 'bg-orange-600 text-white border-orange-600' : 'bg-white text-orange-400 border-orange-300'}`}
                  >
                    {cavaleteIncluido ? '✓ Incluído' : 'Excluído'}
                  </button>
                </div>

                <div className="p-4 space-y-4">
                  {/* Linha de Líquido */}
                  <div>
                    <p className="text-[10px] font-black text-orange-600 uppercase tracking-widest mb-2">Linha de Líquido</p>
                    <div className="space-y-1">
                      {cavaleteResult.linha_liquido.map((it, i) => (
                        <div key={i} className="flex items-center justify-between text-xs py-1 border-b border-orange-50">
                          <span className="text-gray-700">{it.item}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-[10px] text-gray-400">{it.detalhe}</span>
                            <span className="font-bold text-orange-700 w-6 text-right">{it.quantidade}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Linha de Sucção */}
                  <div>
                    <p className="text-[10px] font-black text-orange-600 uppercase tracking-widest mb-2">Linha de Sucção</p>
                    <div className="space-y-1">
                      {cavaleteResult.linha_succao.map((it, i) => (
                        <div key={i} className="flex items-center justify-between text-xs py-1 border-b border-orange-50">
                          <span className="text-gray-700">{it.item}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-[10px] text-gray-400">{it.detalhe}</span>
                            <span className="font-bold text-orange-700 w-6 text-right">{it.quantidade}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Resumo consolidado */}
                  <div className="bg-orange-50 rounded-lg p-3">
                    <p className="text-[10px] font-black text-orange-700 uppercase tracking-widest mb-2">Resumo Consolidado</p>
                    <div className="space-y-1">
                      {cavaleteResult.resumo.map((it, i) => (
                        <div key={i} className="flex justify-between text-xs">
                          <span className="text-gray-700">{it.item}</span>
                          <span className="font-black text-orange-800">{it.quantidade} {it.unidade}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="text-[10px] text-gray-400">
                    Conexão filtro: <b className="capitalize">{cavaleteResult.configuracao.tipo_conexao_filtro}</b> |
                    Visor: <b className="capitalize">{cavaleteResult.configuracao.tipo_conexao_visor}</b> |
                    Linha líquido: <b>{cavaleteResult.configuracao.diametro_liquido}</b> |
                    Linha sucção: <b>{cavaleteResult.configuracao.diametro_succao}</b>
                  </div>
                </div>
              </div>
            )}

            {jaFinalizado && (
              <div className="mb-3 p-3 bg-green-50 border border-green-200 rounded-xl flex items-center gap-3">
                <span className="text-2xl">✅</span>
                <div>
                  <p className="text-sm font-semibold text-green-800">Acessórios carregados do arquivo</p>
                  <p className="text-xs text-green-600">Confirme para ir ao orçamento ou altere os componentes se necessário</p>
                </div>
              </div>
            )}
            <button onClick={finalizar}
              className="w-full py-4 bg-[#7B2D8B] text-white rounded-xl font-bold hover:bg-purple-800 transition-all flex items-center justify-center gap-2 shadow-lg shadow-purple-200">
              CONFIRMAR ACESSÓRIOS E IR PARA ORÇAMENTO ➡️
            </button>
            {jaFinalizado && (
              <p className="text-center text-xs text-slate-400 mt-2">
                💡 Ao confirmar, gere o orçamento novamente no Card 6 para refletir as alterações.
              </p>
            )}
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
