import React, { useState, useEffect, useMemo } from 'react';
import jsPDF from 'jspdf';
import api from '../api';
import PainelInsights from './PainelInsights';

// Vírgula decimal (padrão BR) em vez do "." padrão de JS.
const fmtQtd = (v, casas = 2) => Number(v ?? 0).toLocaleString('pt-BR', { maximumFractionDigits: casas });

// Pizza desenhada num <canvas> off-screen (sem lib de gráfico no projeto —
// mesma técnica já usada em VisualizadorProjeto.jsx pra planta do gabinete),
// devolve PNG base64 pronto pra `pdf.addImage`. Círculo à esquerda, legenda
// com valor + percentual à direita — cabe direto na largura do PDF.
const CORES_CARGA = {
  conducao: '#7B2D8B', infiltracao: '#3B82F6', produto: '#F59E0B',
  respiracao: '#10B981', iluminacao: '#FBBF24', pessoas: '#EF4444', motores: '#6366F1',
};
const gerarImagemPizzaCarga = (fatias) => {
  const H = 480, W = 1150;
  const canvas = document.createElement('canvas');
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, W, H);
  const total = fatias.reduce((s, f) => s + f.valor, 0);
  const cx = H / 2, cy = H / 2, r = H / 2 - 30;
  let anguloAtual = -Math.PI / 2;
  fatias.forEach(f => {
    const fatiaAngulo = (f.valor / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, anguloAtual, anguloAtual + fatiaAngulo);
    ctx.closePath();
    ctx.fillStyle = f.cor;
    ctx.fill();
    anguloAtual += fatiaAngulo;
  });
  let ly = 50;
  const lx = H + 24;
  const larguraDisponivel = W - lx - 30 - 12; // menos o quadrinho de cor + respiro na borda
  ctx.textBaseline = 'middle';
  fatias.forEach(f => {
    const pct = ((f.valor / total) * 100).toFixed(1);
    const texto = `${f.label} — ${Math.round(f.valor).toLocaleString('pt-BR')} kcal/h (${pct}%)`;
    // Reduz a fonte até caber na largura disponível — evita texto cortado
    // quando o rótulo + valor fica comprido (ex: "Condução Térmica").
    let tamanho = 22;
    ctx.font = `bold ${tamanho}px Arial`;
    while (tamanho > 12 && ctx.measureText(texto).width > larguraDisponivel) {
      tamanho -= 1;
      ctx.font = `bold ${tamanho}px Arial`;
    }
    ctx.fillStyle = f.cor;
    ctx.fillRect(lx, ly - 11, 22, 22);
    ctx.fillStyle = '#1e293b';
    ctx.fillText(texto, lx + 30, ly);
    ly += 40;
  });
  return canvas.toDataURL('image/png');
};

const CalculadoraCargaTermica = ({ dadosIniciais, aoFinalizar, initialValues, onValoresChange, jaFinalizado = false, invalidado = false, modoEngenharia = false, projetoAtual = null }) => {
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
  const [horasIluminacao, setHorasIluminacao] = useState(initialValues?.horasIluminacao ?? 8);
  const [pessoas, setPessoas] = useState(initialValues?.pessoas ?? 0);
  const [horasPessoas, setHorasPessoas] = useState(initialValues?.horasPessoas ?? 4);
  const [motor, setMotor] = useState(initialValues?.motor ?? 0);
  const [horasOutrosMotores, setHorasOutrosMotores] = useState(initialValues?.horasOutrosMotores ?? 18);
  const [horasFuncionamento, setHorasFuncionamento] = useState(initialValues?.horasFuncionamento ?? 18);
  const [fatorSeguranca, setFatorSeguranca] = useState(initialValues?.fatorSeguranca ?? 10);

  const [produtoDetalhe, setProdutoDetalhe] = useState(null);

  const [resultado, setResultado] = useState(initialValues?.resultado ?? null);
  const [erro, setErro] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusCalculo, setStatusCalculo] = useState((jaFinalizado || initialValues?.resultado) ? 'pronto' : null);

  useEffect(() => {
    if (onValoresChange) onValoresChange({ movimentacao, tempEntrada, tempoResfriamento, metodoInfiltracao, urExterna, urInterna, iluminacao, horasIluminacao, pessoas, horasPessoas, motor, horasOutrosMotores, horasFuncionamento, fatorSeguranca, categoriaSelecionada, produtoSelecionado, produtoNome: produtoDetalhe?.nome ?? null, resultado });
  }, [movimentacao, tempEntrada, tempoResfriamento, metodoInfiltracao, urExterna, urInterna, iluminacao, horasIluminacao, pessoas, horasPessoas, motor, horasOutrosMotores, horasFuncionamento, fatorSeguranca, categoriaSelecionada, produtoSelecionado, produtoDetalhe, resultado]);

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
      // T.Ambiente é mandatária a partir do Card 1 — antes ficava sempre em 35 fixo aqui.
      if (dadosIniciais.temperatura_ambiente !== undefined) setTempExterna(dadosIniciais.temperatura_ambiente);
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
    metodoInfiltracao, urExterna, urInterna,
    iluminacao, horasIluminacao, pessoas, horasPessoas, motor, horasOutrosMotores,
    horasFuncionamento, fatorSeguranca
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
      horas_iluminacao_dia: parseFloat(horasIluminacao) || 0,
      numero_pessoas: parseFloat(pessoas) || 0,
      horas_pessoas_dia: parseFloat(horasPessoas) || 0,
      potencia_outros_motores_w: parseFloat(motor) || 0,
      horas_outros_motores_dia: parseFloat(horasOutrosMotores) || 0,
      tipo_piso: tipoPiso,
      calcular_infiltracao: true,
      metodo_infiltracao: metodoInfiltracao,
      ur_externa: parseFloat(urExterna) || 60,
      ur_interna: parseFloat(urInterna) || 90,
      fator_seguranca_perc: parseFloat(fatorSeguranca) || 0,
      horas_funcionamento_motor: parseFloat(horasFuncionamento) || 18
    };

    try {
      const response = await api.post('/api/v1/carga-termica', payload);
      setResultado(response.data);
      setStatusCalculo('pronto');
      if (aoFinalizar) aoFinalizar(response.data.capacidade_requerida_equipamento_kcalh);
    } catch (error) {
      console.error("Erro no cálculo:", error);
      setErro(error.response?.data?.erro || 'Erro ao calcular carga térmica.');
    } finally {
      setLoading(false);
    }
  };

  // ── Relatório de Engenharia (Modo Engenharia) ───────────────────────────
  const gerarRelatorioPDF = () => {
    if (!projetoAtual) { setErro('Salve o projeto antes de gerar o relatório — o nome dele entra no cabeçalho.'); return; }
    if (!resultado) return;

    const pdf = new jsPDF('p', 'mm', 'a4');
    const PW = 210, PH = 297, ML = 14, MR = 196, CW = MR - ML;
    let y = 0;
    const novaP = () => { pdf.addPage(); y = 14; };
    const checar = (h = 10) => { if (y + h > PH - 14) novaP(); };
    const txt = (t, x, yy, opts = {}) => pdf.text(String(t ?? ''), x, yy, opts);

    // Cabeçalho
    pdf.setFillColor(15, 23, 42);
    pdf.rect(0, 0, PW, 30, 'F');
    pdf.setTextColor(255, 255, 255);
    pdf.setFontSize(7); pdf.setFont('helvetica', 'bold');
    txt('RELATÓRIO TÉCNICO — CÁLCULO DE CARGA TÉRMICA', ML, 10);
    pdf.setFontSize(15); pdf.setFont('helvetica', 'bold');
    txt(projetoAtual.nome, ML, 19);
    pdf.setFontSize(7); pdf.setFont('helvetica', 'normal');
    txt(`Emitido em ${new Date().toLocaleDateString('pt-BR')}`, ML, 25);
    pdf.setTextColor(0, 0, 0);
    y = 38;

    // Especificações
    pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100);
    txt('ESPECIFICAÇÕES', ML, y); pdf.setTextColor(0); y += 4;
    const specs = [
      ['Dimensões', `${fmtQtd(comprimento)}×${fmtQtd(largura)}×${fmtQtd(altura)} m`],
      ['T. Externa', `${fmtQtd(tempExterna)} °C`],
      ['T. Interna', `${fmtQtd(tempInterna)} °C`],
      ['Isolamento', `${espessura}mm / ${nucleo}`],
      ['Piso', tipoPiso === 'painel' ? 'Painel' : tipoPiso === 'convencional' ? 'Isolado' : 'Sem Isol.'],
    ];
    const colW = CW / specs.length;
    specs.forEach((s, i) => {
      const x = ML + i * colW;
      pdf.setFillColor(241, 245, 249); pdf.rect(x, y, colW - 2, 12, 'F');
      pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100);
      txt(s[0].toUpperCase(), x + 2, y + 4);
      pdf.setFontSize(8); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(0);
      txt(s[1], x + 2, y + 10);
    });
    y += 18;

    // Produto/movimentação, se houver
    if (produtoDetalhe) {
      checar(16);
      pdf.setFillColor(248, 250, 252); pdf.rect(ML, y, CW, 12, 'F');
      pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100);
      txt('PRODUTO E MOVIMENTAÇÃO', ML + 2, y + 4);
      pdf.setFontSize(8); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(0);
      txt(`${produtoDetalhe.nome} · ${fmtQtd(movimentacao)} kg/dia · entrada ${fmtQtd(tempEntrada)}°C · resfriamento ${fmtQtd(tempoResfriamento)}h`, ML + 2, y + 9);
      y += 16;
    }

    // Gráfico de pizza — carga parcial de cada componente
    const fatias = [
      { label: 'Condução Térmica', valor: resultado.carga_conducao_kcalh, cor: CORES_CARGA.conducao },
      { label: 'Infiltração', valor: resultado.carga_infiltracao_kcalh, cor: CORES_CARGA.infiltracao },
      { label: 'Produto/Movimentação', valor: resultado.carga_produto_kcalh, cor: CORES_CARGA.produto },
      { label: 'Respiração', valor: resultado.carga_respiracao_kcalh, cor: CORES_CARGA.respiracao },
      { label: 'Iluminação', valor: resultado.carga_iluminacao_kcalh, cor: CORES_CARGA.iluminacao },
      { label: 'Pessoas', valor: resultado.carga_pessoas_kcalh, cor: CORES_CARGA.pessoas },
      { label: 'Motores/Outros', valor: resultado.carga_motores_kcalh, cor: CORES_CARGA.motores },
    ].filter(f => f.valor > 0);

    if (fatias.length > 0) {
      checar(72);
      pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100);
      txt('DISTRIBUIÇÃO DA CARGA TÉRMICA POR COMPONENTE', ML, y); pdf.setTextColor(0); y += 4;
      const imgW = CW; const imgH = imgW * (480 / 1150);
      pdf.addImage(gerarImagemPizzaCarga(fatias), 'PNG', ML, y, imgW, imgH);
      y += imgH + 6;
    }

    // Tabela detalhada
    checar(14);
    pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100);
    txt('COMPOSIÇÃO DETALHADA DA CARGA', ML, y); pdf.setTextColor(0); y += 4;

    const linhasTabela = [
      ['Condução Térmica', resultado.carga_conducao_kcalh, false],
      resultado.carga_infiltracao_kcalh > 0 ? ['Infiltração por Portas', resultado.carga_infiltracao_kcalh, false] : null,
      ['Produto/Movimentação', resultado.carga_produto_kcalh, false],
      resultado.carga_respiracao_kcalh > 0 ? ['Respiração do Produto', resultado.carga_respiracao_kcalh, false] : null,
      ['— Iluminação', resultado.carga_iluminacao_kcalh, false],
      ['— Pessoas', resultado.carga_pessoas_kcalh, false],
      ['— Motores/Outros', resultado.carga_motores_kcalh, false],
      ['Subtotal Cargas Internas', resultado.carga_internas_total_kcalh, true],
      ['CARGA LÍQUIDA (24h)', resultado.carga_total_24h_kcalh, true],
      [`Fator de Segurança (${resultado.fator_seguranca_aplicado})`, resultado.carga_total_com_seguranca_kcalh - resultado.carga_total_24h_kcalh, false],
      ['CAPACIDADE REQUERIDA DO EQUIPAMENTO', resultado.capacidade_requerida_equipamento_kcalh, true],
    ].filter(Boolean);

    const colLabel = ML, colValor = MR - 45;
    pdf.setFillColor(30, 58, 95); pdf.rect(ML, y, CW, 6, 'F');
    pdf.setFontSize(7); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(255);
    txt('COMPONENTE', colLabel + 2, y + 4); txt('VALOR (kcal/h)', colValor, y + 4);
    pdf.setTextColor(0); y += 6;
    linhasTabela.forEach(([label, valor, destaque], idx) => {
      checar(7);
      if (destaque) { pdf.setFillColor(236, 253, 245); pdf.rect(ML, y, CW, 7, 'F'); }
      else if (idx % 2 === 0) { pdf.setFillColor(248, 250, 252); pdf.rect(ML, y, CW, 7, 'F'); }
      pdf.setFontSize(7.5); pdf.setFont('helvetica', destaque ? 'bold' : 'normal');
      txt(label, colLabel + 2, y + 4.5);
      txt(`${fmtQtd(valor)} kcal/h`, colValor, y + 4.5);
      y += 7;
    });

    checar(10);
    y += 3;
    pdf.setFontSize(7); pdf.setFont('helvetica', 'italic'); pdf.setTextColor(100);
    txt(`Tempo de compressor considerado: ${fmtQtd(resultado.baseado_em_horas_funcionamento)}h/dia`, ML, y);
    pdf.setTextColor(0);

    pdf.save(`Relatorio_CargaTermica_${projetoAtual.nome.replace(/\s+/g, '_')}.pdf`);
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
                  <span className="text-sm font-bold text-slate-700">{produtoDetalhe.temperatura_conservacao !== null ? `${fmtQtd(produtoDetalhe.temperatura_conservacao)}°C` : 'N/A'}</span>
               </div>
               <div className="flex flex-col">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Umidade Relativa</span>
                  <span className="text-sm font-bold text-slate-700">{produtoDetalhe.umidade_relativa !== null ? `${fmtQtd(produtoDetalhe.umidade_relativa)}%` : 'N/A'}</span>
               </div>
               <div className="flex flex-col">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Teor de Água</span>
                  <span className="text-sm font-bold text-slate-700">{produtoDetalhe.teor_agua !== null ? `${fmtQtd(produtoDetalhe.teor_agua)}%` : 'N/A'}</span>
               </div>
               <div className="flex flex-col">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Pto. Congelamento</span>
                  <span className="text-sm font-bold text-slate-700">{fmtQtd(produtoDetalhe.ponto_congelamento)}°C</span>
               </div>
            </div>
          )}
        </div>

        {/* Cargas Internas e Configurações de Tempo */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 min-h-[40px] flex items-center justify-center text-center">Pessoas</label>
            <div className="h-11 flex items-center justify-center gap-3 bg-white border border-slate-200 rounded-xl px-2">
               <button onClick={() => setPessoas(Math.max(0, pessoas - 1))} className="w-8 h-8 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-500">-</button>
               <span className="font-bold text-lg w-8 text-center">{pessoas}</span>
               <button onClick={() => setPessoas(pessoas + 1)} className="w-8 h-8 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-500">+</button>
            </div>
            <input
              type="number"
              value={horasPessoas}
              onChange={e=>setHorasPessoas(e.target.value)}
              min="0" max="24"
              className="w-full h-9 px-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none text-slate-900 text-sm"
            />
            <p className="text-[10px] text-slate-500 text-center">Horas de permanência/dia</p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 min-h-[40px] flex items-center">Iluminação (W)</label>
            <input type="number" value={iluminacao} onChange={e=>setIluminacao(e.target.value)} className="w-full h-11 px-4 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none text-slate-900" />
            <input
              type="number"
              value={horasIluminacao}
              onChange={e=>setHorasIluminacao(e.target.value)}
              min="0" max="24"
              className="w-full h-9 px-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none text-slate-900 text-sm"
            />
            <p className="text-[10px] text-slate-500 text-center">Horas de uso/dia</p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 min-h-[40px] flex items-center">Outros Motores (W)</label>
            <input type="number" value={motor} onChange={e=>setMotor(e.target.value)} className="w-full h-11 px-4 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none text-slate-900" />
            <input
              type="number"
              value={horasOutrosMotores}
              onChange={e=>setHorasOutrosMotores(e.target.value)}
              min="0" max="24"
              className="w-full h-9 px-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 outline-none text-slate-900 text-sm"
            />
            <p className="text-[10px] text-slate-500 text-center">Horas de uso/dia</p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 min-h-[40px] flex items-center">Funcionamento (h/dia)</label>
            <input
              type="number"
              value={horasFuncionamento}
              onChange={e=>setHorasFuncionamento(e.target.value)}
              min="1" max="24"
              className="w-full h-11 px-4 rounded-lg border border-blue-300 bg-blue-50 text-blue-900 font-bold focus:ring-2 focus:ring-blue-500 outline-none"
            />
            <div className="h-9" />
            <p className="text-[9px] text-blue-600 font-bold italic text-center">💡 Recomendado: 16h a 20h</p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 min-h-[40px] flex items-center">Margem de Segurança (%)</label>
            <input
              type="number"
              value={fatorSeguranca}
              onChange={e=>setFatorSeguranca(e.target.value)}
              min="0" max="100"
              className="w-full h-11 px-4 rounded-lg border border-blue-300 bg-blue-50 text-blue-900 font-bold focus:ring-2 focus:ring-blue-500 outline-none"
            />
            <div className="h-9" />
            <p className="text-[9px] text-blue-600 font-bold italic text-center">Aplicada sobre a carga líquida total</p>
          </div>
        </div>


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

        {jaFinalizado && (
          <p className="text-center text-xs text-slate-400 mt-2">
            💡 Ao recalcular, continue pelos próximos cards para manter o projeto consistente.
          </p>
        )}

        {erro && <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm border border-red-200">{erro}</div>}

        {resultado && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="bg-emerald-50 p-6 rounded-2xl border border-emerald-100 flex flex-col justify-center items-center text-center">
              <span className="text-emerald-600 text-xs font-black uppercase tracking-widest mb-1">Capacidade Requerida</span>
              <div className="text-3xl font-black text-emerald-800">{fmtQtd(resultado.capacidade_requerida_equipamento_kcalh)} <small className="text-lg font-normal">kcal/h</small></div>
              <p className="text-emerald-600 text-xs mt-2 font-medium">✅ Valor enviado para seleção de equipamentos</p>
            </div>
            <div className="bg-white p-6 rounded-2xl border border-slate-200">
              <h4 className="text-sm font-bold text-slate-700 mb-3 uppercase tracking-tight">Composição Detalhada da Carga</h4>
              <ul className="space-y-2 text-sm">
                <li className="flex justify-between items-center text-slate-600">
                  <span>Condução Térmica:</span>
                  <span className="font-bold text-slate-900">{fmtQtd(resultado.carga_conducao_kcalh)} kcal/h</span>
                </li>
                {resultado.carga_infiltracao_kcalh > 0 && (
                  <li className="flex flex-col gap-0.5">
                    <div className="flex justify-between items-center text-slate-600">
                      <span>Infiltração por Portas:</span>
                      <span className="font-bold text-slate-900">{fmtQtd(resultado.carga_infiltracao_kcalh)} kcal/h</span>
                    </div>
                    {resultado.info_infiltracao && (
                      <p className="text-[10px] text-slate-400 italic pl-1">{resultado.info_infiltracao}</p>
                    )}
                  </li>
                )}
                <li className="flex justify-between items-center text-slate-600">
                  <span>Produto/Movimentação:</span>
                  <span className="font-bold text-slate-900">{fmtQtd(resultado.carga_produto_kcalh)} kcal/h</span>
                </li>
                {resultado.carga_respiracao_kcalh > 0 && (
                  <li className="flex justify-between items-center text-slate-600">
                    <span>Respiração do Produto:</span>
                    <span className="font-bold text-slate-900">{fmtQtd(resultado.carga_respiracao_kcalh)} kcal/h</span>
                  </li>
                )}

                {/* Detalhamento Interno */}
                <li className="flex justify-between items-center text-slate-400 pt-1 text-[11px] uppercase font-bold">
                  <span>Subtotal Cargas Internas:</span>
                  <span>{fmtQtd(resultado.carga_internas_total_kcalh)} kcal/h</span>
                </li>
                <li className="flex justify-between items-center text-slate-500 pl-4 border-l-2 border-slate-100">
                  <span>Iluminação:</span>
                  <span>{fmtQtd(resultado.carga_iluminacao_kcalh)} kcal/h</span>
                </li>
                <li className="flex justify-between items-center text-slate-500 pl-4 border-l-2 border-slate-100">
                  <span>Pessoas:</span>
                  <span>{fmtQtd(resultado.carga_pessoas_kcalh)} kcal/h</span>
                </li>
                <li className="flex justify-between items-center text-slate-500 pl-4 border-l-2 border-slate-100">
                  <span>Motores/Outros:</span>
                  <span>{fmtQtd(resultado.carga_motores_kcalh)} kcal/h</span>
                </li>

                <li className="flex justify-between items-center pt-2 mt-2 border-t border-slate-200 text-slate-800 font-bold">
                  <span>CARGA LÍQUIDA (24h):</span>
                  <span>{fmtQtd(resultado.carga_total_24h_kcalh)} kcal/h</span>
                </li>
                <li className="flex justify-between items-center text-emerald-600 text-xs italic">
                  <span>Fator de Segurança ({resultado.fator_seguranca_aplicado}):</span>
                  <span>+ {fmtQtd(Math.round(resultado.carga_total_com_seguranca_kcalh - resultado.carga_total_24h_kcalh))} kcal/h</span>
                </li>

                <li className="flex justify-between items-center pt-2 mt-2 border-t border-slate-100 text-blue-600 font-bold">
                  <span>Tempo Compressor:</span>
                  <span>{fmtQtd(resultado.baseado_em_horas_funcionamento)}h/dia</span>
                </li>
              </ul>
            </div>
          </div>
        )}

        {modoEngenharia && resultado && (
          <div className="mt-6 border-t border-slate-200 pt-4">
            <h4 className="text-xs font-bold text-slate-500 uppercase mb-2">📋 Relatório de Engenharia — Card 2</h4>
            {!projetoAtual ? (
              <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                ⚠️ Salve o projeto para poder gerar o relatório — o nome dele entra no cabeçalho.
              </p>
            ) : (
              <button onClick={gerarRelatorioPDF} type="button"
                className="w-full py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-bold shadow-sm transition-colors">
                📄 Relatório PDF — Cálculo de Carga Térmica
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CalculadoraCargaTermica;
