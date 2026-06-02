import React, { useState, useEffect } from 'react';
import api from '../api';
import VisualizadorProjeto from './VisualizadorProjeto';

const CalculadoraGabinete = ({ aoFinalizar }) => {
  // Dimensões da câmara
  const [comprimento, setComprimento] = useState('');
  const [largura, setLargura] = useState('');
  const [altura, setAltura] = useState('');
  const [temperaturaInterna, setTemperaturaInterna] = useState('');
  const [tipoPiso, setTipoPiso] = useState('painel');
  const [espessuraConcreto, setEspessuraConcreto] = useState('');

  // Seleção de painel do catálogo
  const [fabricantes, setFabricantes] = useState([]);
  const [fabricanteSelecionado, setFabricanteSelecionado] = useState('');
  const [paineisFabricante, setPaineisFabricante] = useState([]);   // todos os painéis do fabricante
  const [nucleos, setNucleos] = useState([]);
  const [nucleoSelecionado, setNucleoSelecionado] = useState('');
  const [espessuras, setEspessuras] = useState([]);
  const [espessuraSelecionada, setEspessuraSelecionada] = useState('');
  const [larguras, setLarguras] = useState([]);
  const [larguraSelecionada, setLarguraSelecionada] = useState('');
  const [painelSelecionado, setPainelSelecionado] = useState(null);  // objeto completo

  const [resultado, setResultado] = useState(null);
  const [statusCalculo, setStatusCalculo] = useState(null); // null | 'pronto' | 'modificado'
  const [erro, setErro] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingCAD, setLoadingCAD] = useState(false);
  const [imagemProjeto, setImagemProjeto] = useState(null);
  const [ouvindo, setOuvindo] = useState(false);

  // ── Carregar fabricantes de painéis ao montar ─────────────────────────
  useEffect(() => {
    api.get('/api/v1/catalogo/paineis/fabricantes')
      .then(r => setFabricantes(r.data))
      .catch(() => setFabricantes([]));
  }, []);

  // ── Ao escolher fabricante: carregar painéis e extrair núcleos ────────
  useEffect(() => {
    if (!fabricanteSelecionado) {
      setPaineisFabricante([]); setNucleos([]);
      setNucleoSelecionado(''); setEspessuras([]);
      setEspessuraSelecionada(''); setLarguras([]);
      setLarguraSelecionada(''); setPainelSelecionado(null);
      return;
    }
    api.get(`/api/v1/catalogo/paineis?fabricante_id=${fabricanteSelecionado}`)
      .then(r => {
        setPaineisFabricante(r.data);
        const ns = [...new Set(r.data.map(p => p.nucleo))].sort();
        setNucleos(ns);
        setNucleoSelecionado('');
        setEspessuras([]); setEspessuraSelecionada('');
        setLarguras([]); setLarguraSelecionada('');
        setPainelSelecionado(null);
      })
      .catch(() => setPaineisFabricante([]));
  }, [fabricanteSelecionado]);

  // ── Ao escolher núcleo: filtrar espessuras ────────────────────────────
  useEffect(() => {
    if (!nucleoSelecionado) { setEspessuras([]); setEspessuraSelecionada(''); return; }
    const filtrados = paineisFabricante.filter(p => p.nucleo === nucleoSelecionado);
    const es = [...new Set(filtrados.map(p => p.espessura_mm))].sort((a, b) => a - b);
    setEspessuras(es);
    setEspessuraSelecionada('');
    setLarguras([]); setLarguraSelecionada('');
    setPainelSelecionado(null);
  }, [nucleoSelecionado, paineisFabricante]);

  // ── Ao escolher espessura: filtrar larguras ───────────────────────────
  useEffect(() => {
    if (!espessuraSelecionada) { setLarguras([]); setLarguraSelecionada(''); return; }
    const filtrados = paineisFabricante.filter(
      p => p.nucleo === nucleoSelecionado && p.espessura_mm === parseInt(espessuraSelecionada)
    );
    const ls = [...new Set(filtrados.map(p => p.largura_mm))].sort((a, b) => a - b);
    setLarguras(ls);
    setLarguraSelecionada(ls.length === 1 ? String(ls[0]) : '');
    setPainelSelecionado(ls.length === 1 ? filtrados[0] : null);
  }, [espessuraSelecionada, nucleoSelecionado, paineisFabricante]);

  // ── Ao escolher largura: definir painel final ─────────────────────────
  useEffect(() => {
    if (!larguraSelecionada) { setPainelSelecionado(null); return; }
    const p = paineisFabricante.find(
      p => p.nucleo === nucleoSelecionado &&
           p.espessura_mm === parseInt(espessuraSelecionada) &&
           p.largura_mm   === parseInt(larguraSelecionada)
    );
    setPainelSelecionado(p || null);
  }, [larguraSelecionada, espessuraSelecionada, nucleoSelecionado, paineisFabricante]);

  // ── Detecta edição após cálculo → reseta resultado ───────────────────
  const primeiroRender = React.useRef(true);
  React.useEffect(() => {
    if (primeiroRender.current) { primeiroRender.current = false; return; }
    if (statusCalculo === 'pronto') {
      setStatusCalculo('modificado');
      setResultado(null); // limpa resultado → remove lista_corte → sem scroll indesejado
    }
  }, [comprimento, largura, altura, temperaturaInterna, painelSelecionado, tipoPiso, espessuraConcreto]);

  // ── Sincroniza com pai ────────────────────────────────────────────────
  const dadosParaSincronizar = React.useMemo(() => {
    const base = {
      comprimento: parseFloat(comprimento),
      largura: parseFloat(largura),
      altura: parseFloat(altura),
      temperatura_interna: parseFloat(temperaturaInterna),
      espessura: painelSelecionado ? painelSelecionado.espessura_mm : 100,
      nucleo: painelSelecionado ? painelSelecionado.nucleo : 'PIR',
      u_global: painelSelecionado ? parseFloat(painelSelecionado.u_global) : null,
      tipo_piso: tipoPiso,
      imagem_projeto: imagemProjeto,
    };
    if (!resultado) return base;
    return {
      ...base, ...resultado,
      lista_materiais: [
        ...resultado.lista_corte.map(i => ({ id: null, item: i.item, quantidade: i.quantidade, detalhe: i.descricao, area_total: i.area_total })),
        ...(resultado.materiais_extras || []).map(m => ({ id: null, item: m.item, qtd: m.qtd, detalhe: m.detalhe }))
      ]
    };
  }, [resultado, imagemProjeto, comprimento, largura, altura, temperaturaInterna, painelSelecionado, tipoPiso]);

  const lastSyncRef = React.useRef("");
  React.useEffect(() => {
    if (!aoFinalizar) return;
    const validos = comprimento !== '' && largura !== '' && altura !== '' && temperaturaInterna !== '';
    if (!validos) { aoFinalizar(null); return; }
    const key = JSON.stringify({ res: !!resultado, img: imagemProjeto?.length ?? 0, comprimento, largura, altura, temperaturaInterna, painel: painelSelecionado?.id, tipoPiso });
    if (lastSyncRef.current !== key) { lastSyncRef.current = key; aoFinalizar(dadosParaSincronizar); }
  }, [dadosParaSincronizar, aoFinalizar, resultado, imagemProjeto, comprimento, largura, altura, temperaturaInterna, painelSelecionado, tipoPiso]);

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
        <button onClick={iniciarOuvinteVoz}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold transition-all ${ouvindo ? 'bg-red-500 text-white animate-pulse' : 'bg-white/10 text-white hover:bg-white/20'}`}>
          {ouvindo ? <><span className="w-2 h-2 bg-white rounded-full animate-ping"></span>OUVINDO...</> : <><span>🎤</span> DITAR</>}
        </button>
      </div>

      <div className="p-6">

        {/* Dimensões */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {[['Comprimento (m)', comprimento, setComprimento, 'Ex: 5.00'],
            ['Largura (m)',     largura,     setLargura,     'Ex: 4.00'],
            ['Altura (m)',      altura,      setAltura,      'Ex: 3.00']].map(([label, val, set, ph]) => (
            <div key={label} className="space-y-1">
              <label className="text-sm font-semibold text-slate-700 block">{label}</label>
              <input type="number" value={val} onChange={e => set(e.target.value)} placeholder={ph}
                className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>
          ))}
          <div className="space-y-1">
            <label className="text-sm font-semibold text-slate-700 block">Temperatura Interna (°C)</label>
            <input type="number" value={temperaturaInterna} onChange={e => setTemperaturaInterna(e.target.value)} placeholder="Ex: -18"
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
              <select value={fabricanteSelecionado} onChange={e => setFabricanteSelecionado(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-violet-300 bg-white text-slate-900 focus:ring-2 focus:ring-violet-400 outline-none text-sm">
                <option value="">Selecione...</option>
                {fabricantes.map(f => <option key={f.id} value={f.id}>{f.nome}</option>)}
              </select>
            </div>

            {/* Núcleo */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-500 uppercase block">Núcleo Isolante</label>
              <select value={nucleoSelecionado} onChange={e => setNucleoSelecionado(e.target.value)}
                disabled={!fabricanteSelecionado || nucleos.length === 0}
                className="w-full px-3 py-2 rounded-lg border border-violet-300 bg-white text-slate-900 focus:ring-2 focus:ring-violet-400 outline-none text-sm disabled:opacity-40">
                <option value="">Selecione...</option>
                {nucleos.map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>

            {/* Espessura */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-500 uppercase block">Espessura (mm)</label>
              <select value={espessuraSelecionada} onChange={e => setEspessuraSelecionada(e.target.value)}
                disabled={!nucleoSelecionado || espessuras.length === 0}
                className="w-full px-3 py-2 rounded-lg border border-violet-300 bg-white text-slate-900 focus:ring-2 focus:ring-violet-400 outline-none text-sm disabled:opacity-40">
                <option value="">Selecione...</option>
                {espessuras.map(e => <option key={e} value={e}>{e} mm</option>)}
              </select>
            </div>

            {/* Largura */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-500 uppercase block">Largura do Painel (mm)</label>
              <select value={larguraSelecionada} onChange={e => setLarguraSelecionada(e.target.value)}
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
            <select value={tipoPiso} onChange={e => setTipoPiso(e.target.value)}
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
        </div>

        {/* Botão calcular */}
        <button id="btn-calcular-gabinete" onClick={calcular} disabled={loading}
          className={`w-full py-4 rounded-xl font-bold text-lg shadow-md transition-all flex items-center justify-center gap-2 ${
            loading
              ? 'bg-slate-300 cursor-not-allowed'
              : statusCalculo === 'modificado'
                ? 'bg-amber-500 hover:bg-amber-600 text-white ring-4 ring-amber-100'
                : 'bg-[#7B2D8B] hover:bg-purple-800 text-white hover:-translate-y-0.5'
          }`}>
          {loading ? (
            <><svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>Calculando...</>
          ) : statusCalculo === 'modificado' ? '⚠️ RECALCULAR PROJETO 🔄'
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
        {resultado && (
          <div className="mt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h3 className="text-lg font-bold text-slate-800 mb-4 border-l-4 border-indigo-500 pl-3">Materiais Dimensionados</h3>
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
                  {resultado.lista_corte.map((item, idx) => (
                    <tr key={`c-${idx}`} className="hover:bg-slate-50">
                      <td className="px-4 py-3 text-slate-700 font-medium">{item.item}</td>
                      <td className="px-4 py-3 font-semibold text-slate-900">{item.quantidade}</td>
                      <td className="px-4 py-3 text-right text-slate-500">{item.comprimento}m | {item.area_total}m²</td>
                    </tr>
                  ))}
                  {(resultado.materiais_extras || []).map((item, idx) => (
                    <tr key={`e-${idx}`} className="hover:bg-slate-50 bg-slate-50/30">
                      <td className="px-4 py-3 text-slate-700">
                        <div className="font-medium">{item.item}</div>
                        <div className="text-[10px] text-slate-400 uppercase font-bold">{item.detalhe}</div>
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-900">{item.qtd}</td>
                      <td className="px-4 py-3 text-right text-slate-400 text-xs italic">Material Extra</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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
