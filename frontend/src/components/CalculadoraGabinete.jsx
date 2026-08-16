import React, { useState, useEffect, useRef, useMemo } from 'react';
import api from '../api';
import VisualizadorProjeto from './VisualizadorProjeto';

// Preenchimento por voz (DITAR): frontend pronto, mas depende do endpoint
// POST /api/v1/calculos/processar-voz/, que ainda não existe no backend —
// faz parte do agente IA conversa→orçamento planejado (ver auditoria
// 2026-07-08), ainda não iniciado. Escondido até o backend existir; troque
// para true quando for retomado.
const DITAR_HABILITADO = false;

const CalculadoraGabinete = ({ aoFinalizar, fabricantes = [], portasCatalogo = [], initialValues, onValoresChange, jaFinalizado = false }) => {
  // Dimensões da câmara
  const [comprimento, setComprimento] = useState(initialValues?.comprimento ?? '');
  const [largura, setLargura] = useState(initialValues?.largura ?? '');
  const [altura, setAltura] = useState(initialValues?.altura ?? '');
  const [temperaturaInterna, setTemperaturaInterna] = useState(initialValues?.temperaturaInterna ?? '');
  const [tipoPiso, setTipoPiso] = useState(initialValues?.tipoPiso ?? 'painel');
  const [espessuraConcreto, setEspessuraConcreto] = useState(initialValues?.espessuraConcreto ?? '');
  const [pisoRebaixado, setPisoRebaixado] = useState(initialValues?.pisoRebaixado ?? false);

  // Seleção de painel do catálogo — apenas os 4 valores selecionados são estado
  const [fabricanteSelecionado, setFabricanteSelecionado] = useState(initialValues?.fabricanteSelecionado ?? '');
  const [paineisFabricante, setPaineisFabricante] = useState([]);
  const [nucleoSelecionado,  setNucleoSelecionado]  = useState(initialValues?.nucleoSelecionado  ?? '');
  const [espessuraSelecionada, setEspessuraSelecionada] = useState(initialValues?.espessuraSelecionada ?? '');
  const [larguraSelecionada, setLarguraSelecionada] = useState(initialValues?.larguraSelecionada ?? '');

  // Listas derivadas — calculadas automaticamente de paineisFabricante + seleções
  const nucleos = useMemo(() =>
    [...new Set(paineisFabricante.map(p => p.nucleo))].sort(),
    [paineisFabricante]
  );
  const espessuras = useMemo(() => {
    if (!nucleoSelecionado) return [];
    return [...new Set(
      paineisFabricante.filter(p => p.nucleo === nucleoSelecionado).map(p => p.espessura_mm)
    )].sort((a, b) => a - b);
  }, [paineisFabricante, nucleoSelecionado]);
  const larguras = useMemo(() => {
    if (!nucleoSelecionado || !espessuraSelecionada) return [];
    return [...new Set(
      paineisFabricante
        .filter(p => p.nucleo === nucleoSelecionado && Number(p.espessura_mm) === Number(espessuraSelecionada))
        .map(p => p.largura_mm)
    )].sort((a, b) => a - b);
  }, [paineisFabricante, nucleoSelecionado, espessuraSelecionada]);
  const painelSelecionado = useMemo(() => {
    if (!larguraSelecionada) return null;
    return paineisFabricante.find(p =>
      p.nucleo === nucleoSelecionado &&
      Number(p.espessura_mm) === Number(espessuraSelecionada) &&
      Number(p.largura_mm) === Number(larguraSelecionada)
    ) ?? null;
  }, [paineisFabricante, nucleoSelecionado, espessuraSelecionada, larguraSelecionada]);

  // ── Portas frigoríficas ───────────────────────────────────────────────
  const [portasSelecionadas, setPortasSelecionadas] = useState(initialValues?.portasSelecionadas ?? []);

  // ── Modo de compra dos painéis ────────────────────────────────────────
  // 'fabricante' = sob medida (comprimento exato, preço un/m²)
  // 'revenda'    = barras de comprimento fixo (padrão 12.000mm), técnico corta na obra
  const [modoCompra, setModoCompra] = useState(initialValues?.modoCompra ?? 'fabricante');
  const [comprimentoBarra, setComprimentoBarra] = useState(initialValues?.comprimentoBarra ?? 12000);

  const [resultado, setResultado] = useState(initialValues?.resultado ?? null);
  const [statusCalculo, setStatusCalculo] = useState((jaFinalizado || initialValues?.resultado) ? 'pronto' : null);

  // Snapshot — salva apenas os 4 valores selecionados (as listas são derivadas)
  useEffect(() => {
    if (onValoresChange) onValoresChange({
      comprimento, largura, altura, temperaturaInterna, tipoPiso, espessuraConcreto, pisoRebaixado,
      fabricanteSelecionado, nucleoSelecionado, espessuraSelecionada, larguraSelecionada,
      portasSelecionadas, resultado, modoCompra, comprimentoBarra,
    });
  }, [comprimento, largura, altura, temperaturaInterna, tipoPiso, espessuraConcreto, pisoRebaixado,
      fabricanteSelecionado, nucleoSelecionado, espessuraSelecionada, larguraSelecionada,
      portasSelecionadas, resultado, modoCompra, comprimentoBarra]);
  const [erro, setErro] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingCAD, setLoadingCAD] = useState(false);
  const [imagemProjeto, setImagemProjeto] = useState(null);
  const [ouvindo, setOuvindo] = useState(false);


  // Classificação sugerida baseada na temperatura interna
  const classificacaoSugerida = () => {
    const t = parseFloat(temperaturaInterna);
    if (isNaN(t)) return null;
    if (t < -25) return 'ultra-congelada';
    if (t < -5)  return 'congelada';
    return 'resfriados';
  };

  // Portas filtradas pela classificação sugerida
  const portasFiltradas = portasCatalogo.filter(p => {
    const cs = classificacaoSugerida();
    return cs ? p.classificacao === cs : true;
  });

  const adicionarPorta = (porta) => {
    setPortasSelecionadas(prev => {
      const idx = prev.findIndex(p => p.porta.id === porta.id);
      if (idx >= 0) return prev; // já adicionada
      return [...prev, { porta, qtde: 1 }];
    });
  };

  const removerPorta = (id) =>
    setPortasSelecionadas(prev => prev.filter(p => p.porta.id !== id));

  const updateQtdePorta = (id, qtde) =>
    setPortasSelecionadas(prev =>
      prev.map(p => p.porta.id === id ? { ...p, qtde: Math.max(1, parseInt(qtde) || 1) } : p)
    );

  // ── Fabricante: só carrega dados da API. Seleções downstream são preservadas.
  useEffect(() => {
    if (!fabricanteSelecionado) { setPaineisFabricante([]); return; }
    api.get(`/api/v1/catalogo/paineis?fabricante_id=${fabricanteSelecionado}`)
      .then(r => setPaineisFabricante(r.data))
      .catch(() => setPaineisFabricante([]));
  }, [fabricanteSelecionado]);

  // ── Flag: enquanto true, mudanças de estado são do carregamento, não do usuário ──
  const carregandoDoArquivo = React.useRef(jaFinalizado);

  // ── Handlers que resetam downstream quando o usuário muda a seleção ──
  const handleFabricanteChange = (v) => {
    carregandoDoArquivo.current = false;
    setFabricanteSelecionado(v);
    setNucleoSelecionado('');
    setEspessuraSelecionada('');
    setLarguraSelecionada('');
  };
  const handleNucleoChange = (v) => {
    carregandoDoArquivo.current = false;
    setNucleoSelecionado(v);
    setEspessuraSelecionada('');
    setLarguraSelecionada('');
  };
  const handleEspessuraChange = (v) => {
    carregandoDoArquivo.current = false;
    setEspessuraSelecionada(v);
    const filtrados = paineisFabricante.filter(
      p => p.nucleo === nucleoSelecionado && Number(p.espessura_mm) === Number(v)
    );
    const ls = [...new Set(filtrados.map(p => p.largura_mm))].sort((a, b) => a - b);
    setLarguraSelecionada(ls.length === 1 ? String(ls[0]) : '');
  };
  const handleLarguraChange = (v) => { carregandoDoArquivo.current = false; setLarguraSelecionada(v); };
  const handleInputChange = (setter) => (e) => { carregandoDoArquivo.current = false; setter(e.target.value); };

  // ── Detecta edição após cálculo → reseta resultado ───────────────────
  const primeiroRender = React.useRef(true);
  React.useEffect(() => {
    if (primeiroRender.current) { primeiroRender.current = false; return; }
    if (carregandoDoArquivo.current) return; // mudança vinda do carregamento do arquivo, ignora
    if (statusCalculo === 'pronto') {
      setStatusCalculo('modificado');
      setResultado(null);
    }
  }, [comprimento, largura, altura, temperaturaInterna, painelSelecionado, tipoPiso, espessuraConcreto, pisoRebaixado]);

  // ── Sincroniza com pai ────────────────────────────────────────────────
  // Portas como linhas de material — independentes do cálculo dos painéis
  const portasMateriais = React.useMemo(() => portasSelecionadas.map(({ porta, qtde }) => ({
    id:         porta.id,
    item:       `Porta Frigorífica ${porta.largura_mm}×${porta.altura_mm}mm (${porta.tipo})`,
    tipo_item:  'porta_frigorifica',
    quantidade: qtde,
    unidade:    'un',
    detalhe:    [
      porta.classificacao,
      porta.abertura ? `abertura ${porta.abertura}` : null,
      porta.batente  ? `batente ${porta.batente}`   : null,
      porta.soleira  ? 'com soleira'                : 'sem soleira',
      porta.espessura_mm ? `esp. ${porta.espessura_mm}mm` : null,
    ].filter(Boolean).join(' | '),
  })), [portasSelecionadas]);

  // ── Planejador de corte (modo Revenda) ────────────────────────────────
  // Empacota TODAS as peças de painel (parede+teto+piso, mesmo produto) em
  // barras de comprimento fixo, minimizando o nº de barras (First-Fit-Decreasing).
  const planoCorte = React.useMemo(() => {
    if (!resultado?.lista_corte?.length) return null;
    const barraM = (parseFloat(comprimentoBarra) || 12000) / 1000;
    // largura do painel em metros (do painel selecionado ou derivada de uma peça)
    let larguraM = painelSelecionado ? painelSelecionado.largura_mm / 1000 : null;
    if (!larguraM) {
      const p0 = resultado.lista_corte[0];
      larguraM = (p0.quantidade && p0.comprimento) ? p0.area_total / (p0.quantidade * p0.comprimento) : 1.16;
    }
    // expande em peças individuais {comprimento, origem}
    const pecas = [];
    resultado.lista_corte.forEach(i => {
      const origem = i.item.replace('Painéis de ', '').replace('Painéis ', '');
      for (let k = 0; k < i.quantidade; k++) pecas.push({ comprimento: i.comprimento, origem });
    });
    const grandes = pecas.filter(p => p.comprimento > barraM);
    const cortaveis = pecas.filter(p => p.comprimento <= barraM).sort((a, b) => b.comprimento - a.comprimento);
    // First-Fit-Decreasing
    const barras = [];
    cortaveis.forEach(p => {
      let alvo = barras.find(b => b.restante >= p.comprimento - 1e-9);
      if (!alvo) { alvo = { pecas: [], usado: 0, restante: barraM }; barras.push(alvo); }
      alvo.pecas.push(p); alvo.usado += p.comprimento; alvo.restante -= p.comprimento;
    });
    const sobraTotal = barras.reduce((s, b) => s + b.restante, 0);
    return {
      barraM, larguraM,
      numBarras: barras.length,
      areaBarrasM2: barras.length * barraM * larguraM,
      sobraTotalM: sobraTotal,
      barras: barras.map((b, idx) => ({
        indice: idx + 1,
        pecas: b.pecas,
        usado: b.usado,
        sobra: b.restante,
      })),
      aviso: grandes.length
        ? `${grandes.length} peça(s) de ${grandes[0].comprimento}m excedem a barra de ${barraM}m — não podem ser cortadas de uma única barra.`
        : null,
    };
  }, [resultado, comprimentoBarra, painelSelecionado]);

  const dadosParaSincronizar = React.useMemo(() => {
    const base = {
      comprimento: parseFloat(comprimento),
      largura: parseFloat(largura),
      altura: parseFloat(altura),
      temperatura_interna: parseFloat(temperaturaInterna),
      // Usa espessuraSelecionada diretamente para que o PainelInsights reaja
      // imediatamente à troca, mesmo quando painelSelecionado ainda é null
      // (ex: usuário mudou espessura mas ainda não escolheu largura)
      espessura: painelSelecionado ? painelSelecionado.espessura_mm : (parseInt(espessuraSelecionada) || 100),
      nucleo: painelSelecionado ? painelSelecionado.nucleo : 'PIR',
      u_global: painelSelecionado ? parseFloat(painelSelecionado.u_global) : null,
      tipo_piso: tipoPiso,
      imagem_projeto: imagemProjeto,
    };
    // Sem cálculo de painéis mas com portas: ainda emite a lista com as portas
    if (!resultado) {
      return portasMateriais.length ? { ...base, lista_materiais: [...portasMateriais] } : base;
    }
    const especBase = painelSelecionado
      ? `${painelSelecionado.nucleo} ${painelSelecionado.espessura_mm}mm | larg. ${painelSelecionado.largura_mm}mm | ${painelSelecionado.fabricante?.nome || ''}`
      : '';

    // Modo Revenda: substitui as peças de painel por uma linha de barras de 12m
    const linhasPaineis = (modoCompra === 'revenda' && planoCorte)
      ? [{
          id: null,
          item: `Painel ${base.nucleo} ${base.espessura}mm — Barra ${planoCorte.barraM}m`,
          tipo_item: 'painel_parede',
          quantidade: planoCorte.numBarras,
          unidade: 'un',
          area_total: Number(planoCorte.areaBarrasM2.toFixed(2)),
          detalhe: [
            especBase,
            `${planoCorte.numBarras} barras × ${planoCorte.barraM}m (corte na obra)`,
            `sobra total ${planoCorte.sobraTotalM.toFixed(2)}m`,
          ].filter(Boolean).join(' | '),
        }]
      : resultado.lista_corte.map(i => ({
          id: null,
          item: i.item,
          tipo_item: i.tipo_item ?? null,
          quantidade: i.quantidade,
          unidade: 'un',
          comprimento: i.comprimento,
          area_total: i.area_total,
          detalhe: [i.descricao, especBase].filter(Boolean).join(' | '),
        }));

    return {
      ...base, ...resultado,
      plano_corte: modoCompra === 'revenda' ? planoCorte : null,
      lista_materiais: [
        ...linhasPaineis,
        ...(resultado.materiais_extras || []).map(m => {
          const especPainel = painelSelecionado
            ? `${painelSelecionado.nucleo} ${painelSelecionado.espessura_mm}mm | ${painelSelecionado.fabricante?.nome || ''}`
            : '';
          return {
            id: null,
            item: m.item,
            tipo_item: m.tipo_item ?? null,
            qtd: m.qtd,
            unidade: 'un',
            detalhe: [m.detalhe, especPainel].filter(Boolean).join(' | '),
          };
        }),
        // Portas frigoríficas selecionadas
        ...portasMateriais,
      ]
    };
  }, [resultado, imagemProjeto, comprimento, largura, altura, temperaturaInterna, painelSelecionado, tipoPiso, portasMateriais, modoCompra, planoCorte]);

  const lastSyncRef = React.useRef("");
  React.useEffect(() => {
    if (!aoFinalizar) return;
    const validos = comprimento !== '' && largura !== '' && altura !== '' && temperaturaInterna !== '';
    if (!validos) { aoFinalizar(null); return; }
    // espessuraSelecionada incluída na chave para garantir sync imediato ao trocar espessura
    const portasKey = portasSelecionadas.map(p => `${p.porta.id}x${p.qtde}`).join(',');
    const key = JSON.stringify({ res: !!resultado, img: imagemProjeto?.length ?? 0, comprimento, largura, altura, temperaturaInterna, painel: painelSelecionado?.id, esp: espessuraSelecionada, tipoPiso, rebaixado: pisoRebaixado, portas: portasKey, modoCompra, barra: comprimentoBarra });
    if (lastSyncRef.current !== key) { lastSyncRef.current = key; aoFinalizar(dadosParaSincronizar); }
  }, [dadosParaSincronizar, aoFinalizar, resultado, imagemProjeto, comprimento, largura, altura, temperaturaInterna, painelSelecionado, espessuraSelecionada, tipoPiso, pisoRebaixado, portasSelecionadas, modoCompra, comprimentoBarra]);

  // ── Voz ───────────────────────────────────────────────────────────────
  const iniciarOuvinteVoz = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { setErro("Reconhecimento de voz não suportado."); return; }
    const r = new SR(); r.lang = 'pt-BR'; r.interimResults = false;
    r.onstart = () => setOuvindo(true);
    r.onend   = () => setOuvindo(false);
    r.onresult = async (e) => {
      try {
        setLoading(true);
        const resp = await api.post('/api/v1/calculos/processar-voz/', { texto: e.results[0][0].transcript });
        const d = resp.data.dados_extraidos;
        if (d) {
          if (d.comprimento)      setComprimento(d.comprimento);
          if (d.largura)          setLargura(d.largura);
          if (d.altura)           setAltura(d.altura);
          if (d.temp_interna !== undefined) setTemperaturaInterna(d.temp_interna);
          if (d.tipo_piso)        setTipoPiso(d.tipo_piso);
          setTimeout(() => document.getElementById('btn-calcular-gabinete')?.click(), 500);
        }
      } catch { setErro("Erro ao processar voz."); }
      finally  { setLoading(false); }
    };
    r.start();
  };

  // ── Calcular ──────────────────────────────────────────────────────────
  const calcular = async () => {
    if (!comprimento || !largura || !altura || !temperaturaInterna) {
      setErro('Preencha todas as dimensões e temperatura interna.'); return;
    }
    if (!painelSelecionado) {
      setErro('Selecione o painel frigorífico (fabricante → núcleo → espessura → largura).'); return;
    }
    setLoading(true); setErro('');
    try {
      const response = await api.post('/api/v1/gabinete', {
        comprimento: parseFloat(comprimento),
        largura:     parseFloat(largura),
        altura:      parseFloat(altura),
        temperatura_interna:  parseFloat(temperaturaInterna),
        largura_painel:       painelSelecionado.largura_mm / 1000.0,
        espessura_mm:         painelSelecionado.espessura_mm,
        nucleo:               painelSelecionado.nucleo,
        tipo_piso:            tipoPiso,
        espessura_concreto_cm: parseFloat(espessuraConcreto) || 0,
        piso_rebaixado:       pisoRebaixado,
      });
      setResultado(response.data);
      setStatusCalculo('pronto');
    } catch (error) {
      setErro(error.response?.data?.erro || 'Erro ao calcular. Verifique os dados.');
    } finally { setLoading(false); }
  };

  const baixarDXF = async () => {
    setLoadingCAD(true); setErro('');
    try {
      const response = await api.post('/api/v1/gabinete/dxf/', {
        comprimento, largura, altura,
        largura_painel: painelSelecionado ? painelSelecionado.largura_mm / 1000.0 : 1.1,
        espessura: painelSelecionado?.espessura_mm ?? 100,
      }, { responseType: 'blob' });
      const url  = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url; link.setAttribute('download', `projeto_${comprimento}x${largura}.dxf`);
      document.body.appendChild(link); link.click(); link.remove();
    } catch { setErro('Erro ao gerar DXF.'); }
    finally  { setLoadingCAD(false); }
  };

  // ── Render ────────────────────────────────────────────────────────────
  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden transition-all hover:shadow-xl">
      <div className="bg-gradient-to-r from-[#7B2D8B] to-[#6BBF3F] px-6 py-4 flex justify-between items-center">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span className="bg-white/20 p-1.5 rounded-lg text-lg">📏</span>
          1. Configuração do Gabinete
        </h2>
        {DITAR_HABILITADO && (
          <button onClick={iniciarOuvinteVoz}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold transition-all ${ouvindo ? 'bg-red-500 text-white animate-pulse' : 'bg-white/10 text-white hover:bg-white/20'}`}>
            {ouvindo ? <><span className="w-2 h-2 bg-white rounded-full animate-ping"></span>OUVINDO...</> : <><span>🎤</span> DITAR</>}
          </button>
        )}
      </div>

      <div className="p-6" onFocus={() => { carregandoDoArquivo.current = false; }} onInput={() => { carregandoDoArquivo.current = false; }}>

        {/* Dimensões */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {[['Comprimento (m)', comprimento, setComprimento, 'Ex: 5.00'],
            ['Largura (m)',     largura,     setLargura,     'Ex: 4.00'],
            ['Altura (m)',      altura,      setAltura,      'Ex: 3.00']].map(([label, val, set, ph]) => (
            <div key={label} className="space-y-1">
              <label className="text-sm font-semibold text-slate-700 block">{label}</label>
              <input type="number" value={val} onChange={handleInputChange(set)} placeholder={ph}
                className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>
          ))}
          <div className="space-y-1">
            <label className="text-sm font-semibold text-slate-700 block">Temperatura Interna (°C)</label>
            <input type="number" value={temperaturaInterna} onChange={handleInputChange(setTemperaturaInterna)} placeholder="Ex: -18"
              className="w-full px-4 py-2 rounded-lg border border-blue-200 bg-blue-50 text-blue-900 font-medium focus:ring-2 focus:ring-blue-500 outline-none" />
          </div>
        </div>

        {/* Seleção do Painel Frigorífico */}
        <div className="bg-violet-50 border border-violet-200 rounded-xl p-4 mb-6">
          <h3 className="text-sm font-bold text-violet-800 mb-4 flex items-center gap-2">
            🧱 Painel Frigorífico — Selecione pelo Catálogo
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">

            {/* Fabricante */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-500 uppercase block">Fabricante</label>
              <select value={fabricanteSelecionado} onChange={e => handleFabricanteChange(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-violet-300 bg-white text-slate-900 focus:ring-2 focus:ring-violet-400 outline-none text-sm">
                <option value="">Selecione...</option>
                {fabricantes.map(f => <option key={f.id} value={f.id}>{f.nome}</option>)}
              </select>
            </div>

            {/* Núcleo */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-500 uppercase block">Núcleo Isolante</label>
              <select value={nucleoSelecionado} onChange={e => handleNucleoChange(e.target.value)}
                disabled={!fabricanteSelecionado || nucleos.length === 0}
                className="w-full px-3 py-2 rounded-lg border border-violet-300 bg-white text-slate-900 focus:ring-2 focus:ring-violet-400 outline-none text-sm disabled:opacity-40">
                <option value="">Selecione...</option>
                {nucleos.map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>

            {/* Espessura */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-500 uppercase block">Espessura (mm)</label>
              <select value={espessuraSelecionada} onChange={e => handleEspessuraChange(e.target.value)}
                disabled={!nucleoSelecionado || espessuras.length === 0}
                className="w-full px-3 py-2 rounded-lg border border-violet-300 bg-white text-slate-900 focus:ring-2 focus:ring-violet-400 outline-none text-sm disabled:opacity-40">
                <option value="">Selecione...</option>
                {espessuras.map(e => <option key={e} value={e}>{e} mm</option>)}
              </select>
            </div>

            {/* Largura */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-500 uppercase block">Largura do Painel (mm)</label>
              <select value={larguraSelecionada} onChange={e => handleLarguraChange(e.target.value)}
                disabled={!espessuraSelecionada || larguras.length === 0}
                className="w-full px-3 py-2 rounded-lg border border-violet-300 bg-white text-slate-900 focus:ring-2 focus:ring-violet-400 outline-none text-sm disabled:opacity-40">
                <option value="">Selecione...</option>
                {larguras.map(l => <option key={l} value={l}>{l} mm</option>)}
              </select>
            </div>
          </div>

          {/* Card de dados do painel selecionado */}
          {painelSelecionado ? (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-5 gap-3">
              {[
                ['Núcleo', painelSelecionado.nucleo],
                ['Espessura', `${painelSelecionado.espessura_mm} mm`],
                ['Largura', `${painelSelecionado.largura_mm} mm`],
                ['Comp. Máx.', `${painelSelecionado.comprimento_max_m} m`],
                ['Auto-portância', `${painelSelecionado.auto_portancia_mm} mm`],
                ['Peso', `${painelSelecionado.peso_kg_m2} kg/m²`],
                ['U Global', <span className="text-emerald-700 font-black">{painelSelecionado.u_global} W/(m²·K)</span>],
                ['Fabricante', painelSelecionado.fabricante?.nome ?? ''],
              ].map(([k, v]) => (
                <div key={k} className="bg-white rounded-lg px-3 py-2 border border-violet-100">
                  <p className="text-[10px] text-slate-400 uppercase font-bold">{k}</p>
                  <p className="text-sm font-semibold text-slate-800">{v}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-xs text-violet-500 italic">
              Selecione fabricante → núcleo → espessura → largura para carregar os dados técnicos do painel.
            </p>
          )}
        </div>

        {/* Piso */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="space-y-1">
            <label className="text-sm font-semibold text-slate-700 block">Tipo de Piso</label>
            <select value={tipoPiso} onChange={e => { carregandoDoArquivo.current = false; setTipoPiso(e.target.value); }}
              className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none">
              <option value="painel">Piso em Painel</option>
              <option value="convencional">Piso Isolado (Concreto)</option>
              <option value="nenhum">Sem Isolamento de Piso</option>
            </select>
          </div>
          {tipoPiso === 'convencional' && (
            <div className="space-y-1">
              <label className="text-sm font-semibold text-slate-700 block">Espessura Concreto (cm)</label>
              <input type="number" value={espessuraConcreto} onChange={e => setEspessuraConcreto(e.target.value)}
                placeholder="Ex: 10"
                className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>
          )}
          {tipoPiso === 'convencional' && (
            <label className="md:col-span-2 flex items-start gap-2 cursor-pointer bg-slate-50 border border-slate-200 rounded-lg px-4 py-3">
              <input type="checkbox" checked={pisoRebaixado} onChange={e => setPisoRebaixado(e.target.checked)}
                className="mt-0.5 w-4 h-4 accent-[#7B2D8B]" />
              <span className="text-sm text-slate-700">
                <span className="font-semibold">Piso rebaixado</span> (nivelado, sem degrau)
                <span className="block text-xs text-slate-500">
                  Abre rebaixo para isolamento + concreto → piso interno nivelado com o externo.
                  A parede desce no rebaixo (fica mais comprida) e a altura útil = altura − teto.
                </span>
              </span>
            </label>
          )}
        </div>

        {/* ── Seção de Portas Frigoríficas ── */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-slate-700 flex items-center gap-2">
              🚪 Portas Frigoríficas
            </h3>
            {classificacaoSugerida() && (
              <span className="text-[10px] bg-blue-100 text-blue-700 font-bold px-2 py-1 rounded-full uppercase">
                Sugerido: {classificacaoSugerida()}
              </span>
            )}
          </div>

          {/* Catálogo de portas disponíveis */}
          {portasFiltradas.length === 0 ? (
            <p className="text-xs text-slate-400 italic">
              {portasCatalogo.length === 0
                ? 'Nenhuma porta cadastrada no catálogo.'
                : `Nenhuma porta para classificação "${classificacaoSugerida()}". Veja outras abaixo.`}
            </p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
              {portasCatalogo.map(porta => {
                const jaSelecionada = portasSelecionadas.some(p => p.porta.id === porta.id);
                const sugerida = porta.classificacao === classificacaoSugerida();
                return (
                  <button key={porta.id} onClick={() => !jaSelecionada && adicionarPorta(porta)}
                    disabled={jaSelecionada}
                    className={`flex items-center justify-between p-3 rounded-lg border text-left transition-all text-xs ${
                      jaSelecionada
                        ? 'border-emerald-300 bg-emerald-50 opacity-60 cursor-not-allowed'
                        : sugerida
                          ? 'border-blue-300 bg-blue-50 hover:border-blue-400 cursor-pointer'
                          : 'border-slate-200 bg-white hover:border-slate-400 cursor-pointer'
                    }`}
                  >
                    <div>
                      <p className="font-bold text-slate-700">
                        {porta.largura_mm}×{porta.altura_mm}mm — {porta.tipo}
                      </p>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        {porta.classificacao} | esp. {porta.espessura_mm}mm
                        {porta.abertura && ` | ${porta.abertura}`}
                        {porta.batente  && ` | ${porta.batente}`}
                        {porta.soleira  ? ' | com soleira' : ''}
                      </p>
                    </div>
                    <span className={`ml-2 flex-shrink-0 text-lg ${jaSelecionada ? 'text-emerald-500' : 'text-slate-300'}`}>
                      {jaSelecionada ? '✓' : '+'}
                    </span>
                  </button>
                );
              })}
            </div>
          )}

          {/* Portas selecionadas com quantidade */}
          {portasSelecionadas.length > 0 && (
            <div className="border-t border-slate-200 pt-3 space-y-2">
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Portas no projeto</p>
              {portasSelecionadas.map(({ porta, qtde }) => (
                <div key={porta.id} className="flex items-center gap-3 bg-white border border-emerald-200 rounded-lg px-3 py-2">
                  <div className="flex-1 text-xs">
                    <span className="font-bold text-slate-700">
                      {porta.largura_mm}×{porta.altura_mm}mm — {porta.tipo}
                    </span>
                    <span className="text-slate-400 ml-1">({porta.classificacao})</span>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <label className="text-[10px] text-slate-500">Qtde:</label>
                    <input type="number" min="1" value={qtde}
                      onChange={e => updateQtdePorta(porta.id, e.target.value)}
                      className="w-14 px-2 py-1 rounded border border-slate-300 text-center text-xs outline-none" />
                    <button onClick={() => removerPorta(porta.id)}
                      className="text-slate-300 hover:text-red-400 transition-colors text-sm">✕</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Banner projeto carregado */}
        {jaFinalizado && !resultado && statusCalculo === 'pronto' && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-xl flex items-center gap-3">
            <span className="text-2xl">✅</span>
            <div>
              <p className="text-sm font-semibold text-green-800">Gabinete calculado — dados carregados do arquivo</p>
              <p className="text-xs text-green-600">Clique em "Recalcular" para atualizar os resultados detalhados</p>
            </div>
          </div>
        )}

        {/* Botão calcular */}
        <button id="btn-calcular-gabinete" onClick={calcular} disabled={loading}
          className={`w-full py-4 rounded-xl font-bold text-lg shadow-md transition-all flex items-center justify-center gap-2 ${
            loading
              ? 'bg-slate-300 cursor-not-allowed'
              : statusCalculo === 'modificado'
                ? 'bg-amber-500 hover:bg-amber-600 text-white ring-4 ring-amber-100'
                : statusCalculo === 'pronto' && !resultado
                  ? 'bg-green-600 hover:bg-green-700 text-white hover:-translate-y-0.5'
                  : 'bg-[#7B2D8B] hover:bg-purple-800 text-white hover:-translate-y-0.5'
          }`}>
          {loading ? (
            <><svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>Calculando...</>
          ) : statusCalculo === 'modificado' ? '⚠️ RECALCULAR PROJETO 🔄'
          : statusCalculo === 'pronto' && !resultado ? '🔄 Recalcular Projeto'
          : 'CALCULAR PROJETO ➡️'}
        </button>

        {erro && <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm border border-red-200">{erro}</div>}

        {/* Visualizador + DXF */}
        <div className="mt-8">
          <VisualizadorProjeto
            dimensoes={{ comp: comprimento, larg: largura, alt: altura }}
            larguraPainel={painelSelecionado?.largura_mm ?? 1100}
            espessura={painelSelecionado?.espessura_mm ?? 100}
            onImagemGerada={setImagemProjeto}
          />
          <button onClick={baixarDXF} disabled={loadingCAD || !resultado}
            className={`w-full mt-4 py-3 rounded-xl font-bold text-sm shadow-sm transition-all flex items-center justify-center gap-2 ${loadingCAD || !resultado ? 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200' : 'bg-white text-indigo-600 border-2 border-indigo-600 hover:bg-indigo-50'}`}>
            {loadingCAD ? 'Gerando CAD...' : <><span>📥</span> BAIXAR PROJETO CAD (.DXF)</>}
          </button>
        </div>

        {/* Resultados */}
        {(resultado || portasSelecionadas.length > 0) && (
          <div className="mt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h3 className="text-lg font-bold text-slate-800 mb-4 border-l-4 border-indigo-500 pl-3">Materiais Dimensionados</h3>

            {/* Modo de compra dos painéis */}
            {resultado && (
              <div className="mb-4 p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <p className="text-[10px] font-bold text-slate-400 uppercase mb-2">Compra dos painéis</p>
                <div className="flex flex-wrap items-center gap-2">
                  {[
                    { v: 'fabricante', label: 'Fabricante (sob medida)', desc: 'Cortado na medida do projeto' },
                    { v: 'revenda',    label: 'Revenda (barra 12m)',     desc: 'Barras cortadas na obra' },
                  ].map(opt => (
                    <label key={opt.v} className={`flex items-start gap-2 p-2.5 rounded-lg border cursor-pointer text-xs flex-1 min-w-[180px] transition-all ${modoCompra === opt.v ? 'bg-indigo-50 border-indigo-300' : 'bg-white border-slate-200'}`}>
                      <input type="radio" checked={modoCompra === opt.v} onChange={() => setModoCompra(opt.v)} className="accent-indigo-600 mt-0.5" />
                      <span><b>{opt.label}</b><br /><span className="text-slate-500">{opt.desc}</span></span>
                    </label>
                  ))}
                  {modoCompra === 'revenda' && (
                    <div className="flex items-center gap-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase">Barra (mm)</label>
                      <input type="number" min="1000" step="500" value={comprimentoBarra}
                        onChange={e => setComprimentoBarra(parseInt(e.target.value) || 12000)}
                        className="w-24 px-2 py-1.5 rounded-lg border border-slate-300 text-xs text-center outline-none focus:ring-2 focus:ring-indigo-400" />
                    </div>
                  )}
                </div>
                {modoCompra === 'revenda' && planoCorte && (
                  <p className="text-[11px] text-indigo-600 mt-2 font-medium">
                    {planoCorte.numBarras} barras de {planoCorte.barraM}m ({planoCorte.areaBarrasM2.toFixed(1)} m²) · sobra total {planoCorte.sobraTotalM.toFixed(2)}m entregue ao cliente
                  </p>
                )}
                {planoCorte?.aviso && (
                  <p className="text-[11px] text-red-500 mt-1">⚠ {planoCorte.aviso}</p>
                )}
              </div>
            )}

            <div className="overflow-hidden border border-slate-200 rounded-xl">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50">
                    <th className="px-4 py-3 text-sm font-bold text-slate-600">Item</th>
                    <th className="px-4 py-3 text-sm font-bold text-slate-600">Qtd</th>
                    <th className="px-4 py-3 text-sm font-bold text-slate-600 text-right">Medida / Área</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {modoCompra === 'revenda' && planoCorte ? (
                    <tr className="hover:bg-slate-50 bg-indigo-50/40">
                      <td className="px-4 py-3 text-slate-700">
                        <div className="font-medium">Painel {resultado?.nucleo_selecionado || ''} — Barra {planoCorte.barraM}m</div>
                        <div className="text-[10px] text-slate-400 uppercase font-bold">Corte na obra · sobra {planoCorte.sobraTotalM.toFixed(2)}m</div>
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-900">{planoCorte.numBarras}</td>
                      <td className="px-4 py-3 text-right text-indigo-500 text-xs italic">{planoCorte.areaBarrasM2.toFixed(1)} m² (barras)</td>
                    </tr>
                  ) : (resultado?.lista_corte || []).map((item, idx) => (
                    <tr key={`c-${idx}`} className="hover:bg-slate-50">
                      <td className="px-4 py-3 text-slate-700 font-medium">{item.item}</td>
                      <td className="px-4 py-3 font-semibold text-slate-900">{item.quantidade}</td>
                      <td className="px-4 py-3 text-right text-slate-500">{item.comprimento}m | {item.area_total}m²</td>
                    </tr>
                  ))}
                  {(resultado?.materiais_extras || []).map((item, idx) => (
                    <tr key={`e-${idx}`} className="hover:bg-slate-50 bg-slate-50/30">
                      <td className="px-4 py-3 text-slate-700">
                        <div className="font-medium">{item.item}</div>
                        <div className="text-[10px] text-slate-400 uppercase font-bold">{item.detalhe}</div>
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-900">{item.qtd}</td>
                      <td className="px-4 py-3 text-right text-slate-400 text-xs italic">Material Extra</td>
                    </tr>
                  ))}
                  {portasMateriais.map((p, idx) => (
                    <tr key={`p-${idx}`} className="hover:bg-slate-50 bg-amber-50/40">
                      <td className="px-4 py-3 text-slate-700">
                        <div className="font-medium">{p.item}</div>
                        <div className="text-[10px] text-slate-400 uppercase font-bold">{p.detalhe}</div>
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-900">{p.quantidade}</td>
                      <td className="px-4 py-3 text-right text-amber-500 text-xs italic">Porta Frigorífica</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {/* Mapa de corte — modo Revenda */}
            {modoCompra === 'revenda' && planoCorte && (
              <div className="mt-4 border border-indigo-100 rounded-xl overflow-hidden">
                <div className="bg-indigo-50 px-4 py-2 flex items-center justify-between">
                  <span className="text-xs font-black text-indigo-700 uppercase tracking-wide">Mapa de corte — {planoCorte.numBarras} barras de {planoCorte.barraM}m</span>
                  <span className="text-[11px] text-indigo-500">sobra total {planoCorte.sobraTotalM.toFixed(2)}m</span>
                </div>
                <div className="divide-y divide-slate-100 max-h-72 overflow-y-auto">
                  {planoCorte.barras.map(b => (
                    <div key={b.indice} className="flex items-center gap-3 px-4 py-2 text-xs">
                      <span className="font-bold text-slate-400 w-14">Barra {b.indice}</span>
                      <div className="flex-1 flex flex-wrap gap-1">
                        {b.pecas.map((p, i) => (
                          <span key={i} className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
                            {p.comprimento}m <span className="text-slate-400">({p.origem})</span>
                          </span>
                        ))}
                        {b.sobra > 0.01 && (
                          <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-500 italic">sobra {b.sobra.toFixed(2)}m</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-4 p-4 bg-green-50 border border-green-100 rounded-xl text-green-700 flex items-center gap-2">
              <span className="text-xl">✅</span>
              <span className="text-sm font-medium">Dados enviados para o próximo passo!</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CalculadoraGabinete;
