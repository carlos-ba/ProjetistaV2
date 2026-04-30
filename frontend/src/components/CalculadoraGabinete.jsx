import React, { useState } from 'react';
import api from '../api';
import VisualizadorProjeto from './VisualizadorProjeto';
import PainelInsights from './PainelInsights';

const CalculadoraGabinete = ({ aoFinalizar }) => {
  const [comprimento, setComprimento] = useState('');
  const [largura, setLargura] = useState('');
  const [altura, setAltura] = useState('');
  const [temperaturaInterna, setTemperaturaInterna] = useState('');
  const [larguraPainel, setLarguraPainel] = useState('');
  const [espessura, setEspessura] = useState(100);
  const [nucleo, setNucleo] = useState('PUR');
  const [tipoPiso, setTipoPiso] = useState('painel');
  const [espessuraConcreto, setEspessuraConcreto] = useState('');
  const [resultado, setResultado] = useState(null);
  const [erro, setErro] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingCAD, setLoadingCAD] = useState(false);
  const [imagemProjeto, setImagemProjeto] = useState(null);

  // Sincroniza dados com o componente pai sempre que houver mudanças
  // Usamos useMemo para evitar recriar o objeto de materiais a cada render e causar loops
  const dadosParaSincronizar = React.useMemo(() => {
    const base = {
      comprimento: parseFloat(comprimento), 
      largura: parseFloat(largura), 
      altura: parseFloat(altura), 
      temperatura_interna: parseFloat(temperaturaInterna),
      espessura: parseFloat(espessura),
      nucleo,
      tipo_piso: tipoPiso,
      imagem_projeto: imagemProjeto,
    };

    if (!resultado) return base;

    return {
      ...base,
      ...resultado,
      lista_materiais: [
        ...resultado.lista_corte.map(i => ({
          id: null,
          item: i.item,
          quantidade: i.quantidade,
          detalhe: i.descricao,
          area_total: i.area_total
        })),
        ...(resultado.materiais_extras || []).map(m => ({
          id: null,
          item: m.item,
          qtd: m.qtd,
          detalhe: m.detalhe
        }))
      ]
    };
  }, [resultado, imagemProjeto, comprimento, largura, altura, temperaturaInterna, espessura, nucleo, tipoPiso]);

  // Controle para evitar loop infinito de sincronização
  const lastSyncRef = React.useRef("");

  React.useEffect(() => {
    if (!aoFinalizar) return;

    const camposValidos = comprimento !== '' && largura !== '' && altura !== '' && temperaturaInterna !== '';

    if (!camposValidos) {
      aoFinalizar(null);
      return;
    }

    const currentSyncKey = JSON.stringify({
      res: !!resultado,
      img: imagemProjeto ? imagemProjeto.length : 0,
      c: comprimento,
      l: largura,
      a: altura,
      e: espessura,
      n: nucleo,
      t: temperaturaInterna,
      p: tipoPiso
    });

    if (lastSyncRef.current !== currentSyncKey) {
      lastSyncRef.current = currentSyncKey;
      aoFinalizar(dadosParaSincronizar);
    }
  }, [dadosParaSincronizar, aoFinalizar, resultado, imagemProjeto, comprimento, largura, altura, espessura, nucleo, temperaturaInterna, tipoPiso]);

  // --- ESTADOS DE VOZ ---
  const [ouvindo, setOuvindo] = useState(false);

  const iniciarOuvinteVoz = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setErro("Reconhecimento de voz não suportado neste navegador.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'pt-BR';
    recognition.interimResults = false;

    recognition.onstart = () => setOuvindo(true);
    recognition.onend = () => setOuvindo(false);

    recognition.onresult = async (event) => {
      const texto = event.results[0][0].transcript;
      console.log("Voz capturada:", texto);
      
      try {
        setLoading(true);
        const resp = await api.post('/api/v1/calculos/processar-voz/', { texto });
        const dados = resp.data.dados_extraidos;

        if (dados) {
          if (dados.comprimento) setComprimento(dados.comprimento);
          if (dados.largura) setLargura(dados.largura);
          if (dados.altura) setAltura(dados.altura);
          if (dados.temp_interna !== undefined) setTemperaturaInterna(dados.temp_interna);
          if (dados.espessura_mm) setEspessura(dados.espessura_mm);
          if (dados.nucleo) setNucleo(dados.nucleo);
          if (dados.tipo_piso) setTipoPiso(dados.tipo_piso);

          // Aciona o cálculo automaticamente após preencher os dados
          // Usamos um pequeno timeout para garantir que os estados do React foram "agendados"
          setTimeout(() => {
            document.getElementById('btn-calcular-gabinete')?.click();
          }, 500);
        }
      } catch (err) {
        setErro("Erro ao processar comando de voz.");
      } finally {
        setLoading(false);
      }
    };

    recognition.start();
  };

  const calcular = async () => {
    const c = parseFloat(comprimento);
    const l = parseFloat(largura);
    const a = parseFloat(altura);
    const lp = parseFloat(larguraPainel);
    const e = parseFloat(espessura);

    const t = parseFloat(temperaturaInterna);
    if (!c || !l || !a || !lp || !e || isNaN(t)) {
      setErro('Por favor, preencha todas as dimensões com valores válidos antes de calcular.');
      return;
    }

    setLoading(true);
    setErro('');
    try {
      const response = await api.post('/api/v1/gabinete', {
        comprimento: c,
        largura: l,
        altura: a,
        temperatura_interna: parseFloat(temperaturaInterna),
        largura_painel: lp / 1000.0,
        espessura_mm: e,
        nucleo: nucleo,
        tipo_piso: tipoPiso,
        espessura_concreto_cm: parseFloat(espessuraConcreto) || 0
      });
      setResultado(response.data);
    } catch (error) {
      console.error(error);
      if (error.response && error.response.data && error.response.data.erro) {
        setErro(`Erro: ${error.response.data.erro}`);
      } else {
        setErro('Erro ao calcular. Verifique se o servidor está rodando ou os dados são válidos.');
      }
    } finally {
      setLoading(false);
    }
  };

  const baixarDXF = async () => {
    setLoadingCAD(true);
    setErro('');
    try {
      const response = await api.post('/api/v1/gabinete/dxf/', {
        comprimento, largura, altura, 
        largura_painel: parseFloat(larguraPainel) / 1000.0,
        espessura
      }, { responseType: 'blob' });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `projeto_camara_${comprimento}x${largura}.dxf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error(error);
      setErro('Erro ao gerar arquivo DXF. Verifique o console ou o servidor.');
    } finally {
      setLoadingCAD(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden transition-all hover:shadow-xl">
      <div className="bg-gradient-to-r from-[#7B2D8B] to-[#6BBF3F] px-6 py-4 flex justify-between items-center">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span className="bg-white/20 p-1.5 rounded-lg text-lg">📏</span>
          1. Configuração do Gabinete
        </h2>
        
        {/* BOTÃO DE VOZ */}
        <button 
          onClick={iniciarOuvinteVoz}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold transition-all ${
            ouvindo 
              ? 'bg-red-500 text-white animate-pulse shadow-lg shadow-red-200' 
              : 'bg-white/10 text-white hover:bg-white/20'
          }`}
        >
          {ouvindo ? (
            <>
              <span className="w-2 h-2 bg-white rounded-full animate-ping"></span>
              OUVINDO...
            </>
          ) : (
            <>
              <span>🎤</span> DITAR PROJETO
            </>
          )}
        </button>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Inputs de Dimensões */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Comprimento (m)</label>
            <input
              type="number" value={comprimento} onChange={e => setComprimento(e.target.value)}
              placeholder="Ex: 5.00"
              className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Largura (m)</label>
            <input
              type="number" value={largura} onChange={e => setLargura(e.target.value)}
              placeholder="Ex: 4.00"
              className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Altura (m)</label>
            <input
              type="number" value={altura} onChange={e => setAltura(e.target.value)}
              placeholder="Ex: 3.00"
              className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            />
          </div>

          {/* Temperatura e Isolamento */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Temperatura Interna (°C)</label>
            <input
              type="number" value={temperaturaInterna} onChange={e => setTemperaturaInterna(e.target.value)}
              placeholder="Ex: -18"
              className="w-full px-4 py-2 rounded-lg border border-blue-200 bg-blue-50 text-blue-900 font-medium focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Espessura Painel (mm)</label>
            <select 
              value={espessura} onChange={e => setEspessura(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            >
              {[50, 70, 100, 120, 150, 200].map(v => <option key={v} value={v}>{v}mm</option>)}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Núcleo Isolante</label>
            <select 
              value={nucleo} onChange={e => setNucleo(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            >
              <option value="PUR">PUR (Poliuretano)</option>
              <option value="PIR">PIR (Poliisocianurato)</option>
              <option value="EPS">EPS (Isopor)</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Largura do Painel (mm)</label>
            <input
              type="number" value={larguraPainel} onChange={e => setLarguraPainel(e.target.value)}
              placeholder="Ex: 1150"
              className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 block">Tipo de Piso</label>
            <select 
              value={tipoPiso} onChange={e => setTipoPiso(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            >
              <option value="painel">Piso em Painel</option>
              <option value="convencional">Piso Isolado (Concreto)</option>
              <option value="nenhum">Sem Isolamento de Piso</option>
            </select>
          </div>
          {tipoPiso === 'convencional' && (
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700 block">Espessura Concreto (cm)</label>
              <input
                type="number" value={espessuraConcreto} onChange={e => setEspessuraConcreto(e.target.value)}
                placeholder="Ex: 10"
                className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
              />
            </div>
          )}
        </div>

        <button 
          id="btn-calcular-gabinete"
          onClick={calcular} 
          disabled={loading}
          className={`w-full py-4 rounded-xl font-bold text-lg shadow-md transition-all flex items-center justify-center gap-2 ${
            loading ? 'bg-slate-300 cursor-not-allowed' : 'bg-[#7B2D8B] hover:bg-purple-800 text-white hover:-translate-y-0.5 active:translate-y-0'
          }`}
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Calculando...
            </>
          ) : 'CALCULAR PROJETO ➡️'}
        </button>

        {erro && <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm border border-red-200">{erro}</div>}

        <div className="mt-8 space-y-8">
          {/* Visualizador em Linha Única */}
          <div className="w-full">
            <VisualizadorProjeto 
              dimensoes={{ comp: comprimento, larg: largura, alt: altura }}
              larguraPainel={larguraPainel}
              espessura={espessura}
              onImagemGerada={setImagemProjeto}
            />
            
            <button
              onClick={baixarDXF}
              disabled={loadingCAD || !resultado}
              className={`w-full mt-4 py-3 rounded-xl font-bold text-sm shadow-sm transition-all flex items-center justify-center gap-2 ${
                loadingCAD || !resultado 
                  ? 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200' 
                  : 'bg-white text-indigo-600 border-2 border-indigo-600 hover:bg-indigo-50'
              }`}
            >
              {loadingCAD ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-indigo-600" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Gerando CAD...
                </>
              ) : (
                <>
                  <span>📥</span> BAIXAR PROJETO CAD (.DXF)
                </>
              )}
            </button>
          </div>
        </div>

        {/* Tabela de Resultados Estilizada */}
        {resultado && (
          <div className="mt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h3 className="text-lg font-bold text-slate-800 mb-4 border-l-4 border-indigo-500 pl-3">Materiais Dimensionados</h3>
            <div className="overflow-hidden border border-slate-200 rounded-xl">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-bottom border-slate-200">
                    <th className="px-4 py-3 text-sm font-bold text-slate-600">Item</th>
                    <th className="px-4 py-3 text-sm font-bold text-slate-600">Qtd</th>
                    <th className="px-4 py-3 text-sm font-bold text-slate-600 text-right">Medida/Área</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {/* Itens de Corte (Painéis) */}
                  {resultado.lista_corte.map((item, idx) => (
                    <tr key={`corte-${idx}`} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 text-slate-700 font-medium">{item.item}</td>
                      <td className="px-4 py-3 font-semibold text-slate-900">{item.quantidade}</td>
                      <td className="px-4 py-3 text-right text-slate-500">{item.comprimento}m | {item.area_total}m²</td>
                    </tr>
                  ))}

                  {/* Materiais Extras (Piso, Acessórios, etc) */}
                  {resultado.materiais_extras && resultado.materiais_extras.map((item, idx) => (
                    <tr key={`extra-${idx}`} className="hover:bg-slate-50 transition-colors bg-slate-50/30">
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
