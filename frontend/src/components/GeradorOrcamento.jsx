import React, { useState, useEffect, useRef, useMemo } from 'react';
import api from '../api';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import ExcelJS from 'exceljs';
import ModalCotacaoFornecedor from './ModalCotacaoFornecedor';

// ── Linha de complemento em branco ───────────────────────────────────────
const novoComplemento = () => ({ descricao: '', qtde: 1, unidade: 'un', preco_unit: '', classificacao_id: null });

const norm = (s) => (s || '').toLowerCase().trim().replace(/\s+/g, ' ');

const fmt = (v) => (v ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// Quantidades (m², kg, un, m) — vírgula decimal (padrão BR), sem casas decimais forçadas
// em número inteiro (10, não 10,00). Interpolação direta de número em template string
// usa "." (padrão JS), o que confunde no campo — sempre passar por aqui.
const fmtQtd = (v) => Number(v ?? 0).toLocaleString('pt-BR', { maximumFractionDigits: 2 });

const CONDICOES_PADRAO = {
  pagamento: '40% na aprovação do pedido · 40% na entrega dos materiais · 20% na entrega técnica',
  validade_dias: 10,
  prazo_execucao: '30 dias corridos após confirmação do pedido',
  garantia: '12 meses para os serviços de instalação. Equipamentos: garantia de fábrica do fabricante.',
  incluso: 'Fornecimento e montagem dos painéis frigoríficos; instalação do sistema de refrigeração; tubulações frigorígenas e elétricas entre evaporador e unidade condensadora; vácuo, carga de fluido e entrega técnica com câmara em temperatura.',
  nao_incluso: 'Obras civis e base nivelada; alimentação elétrica até o ponto da unidade condensadora; disjuntores e quadro geral; descarte de entulho; taxas e licenças.',
};

// ── Cores por bloco — Proposta ao Cliente (faturamento direto, lista completa) ──
// Uma cor por bloco (nome vem de bloco_orcamento no banco), igual na lista
// itemizada e no resumo de investimento. Mão de obra tem cor própria, fora
// dessa paleta, pois não é um bloco de material. `rgb` mantém o hex do
// Tailwind equivalente pra o PDF (jsPDF não lê classes CSS).
const CORES_BLOCO = {
  'Materiais Termo Isolantes': { dot: 'bg-sky-500',     texto: 'text-sky-700',     rgb: [2, 132, 199] },
  'Equipamentos':              { dot: 'bg-emerald-500', texto: 'text-emerald-700', rgb: [5, 150, 105] },
  'Tubulação e Conexões':      { dot: 'bg-amber-500',   texto: 'text-amber-700',   rgb: [217, 119, 6] },
  'Componentes de Fluxo':      { dot: 'bg-violet-500',  texto: 'text-violet-700',  rgb: [124, 58, 237] },
};
const COR_BLOCO_PADRAO = { dot: 'bg-slate-400', texto: 'text-slate-500', rgb: [100, 116, 139] }; // "Outros" ou bloco não mapeado
const COR_MAO_DE_OBRA = { dot: 'bg-rose-500', texto: 'text-rose-700', rgb: [225, 29, 72] };
const corDoBloco = (nome) => CORES_BLOCO[nome] || COR_BLOCO_PADRAO;

const GeradorOrcamento = ({ dadosAutomaticos, aoRemoverEquipamento, aoReiniciar, projetoAtual = null, onClienteChange, initialValues, onValoresChange, aoConfirmar, onAbrirPainelCotacoes, resumoTecnico = null, triggerGerarProposta = 0, onSalvarProjeto, onSalvarComo, classificacoes = null, modoEngenharia = false, embalagensFluido = [], onAbrirClassificacoes = null, bloqueadoTrial = false }) => {
  const projetoSalvo = !!projetoAtual?.id;
  const propostaRef = useRef(null);

  // ── Resolução de classificação (via banco) ────────────────────────────
  // Constrói índices a partir da árvore carregada no App: mapa tipo_item→classificação,
  // classificação→bloco. Fonte única para a lista E para os blocos financeiros.
  const classIndex = React.useMemo(() => {
    const blocos = classificacoes?.blocos || [];
    const classes = classificacoes?.classificacoes || [];
    const mapa = classificacoes?.mapa || {};
    const blocoPorId = Object.fromEntries(blocos.map(b => [b.id, b]));
    const classePorId = Object.fromEntries(classes.map(c => [c.id, c]));
    const ordemBloco = Object.fromEntries(blocos.map(b => [b.nome, b.ordem]));
    // Nome do bloco (nível 1) a partir de um item do orçamento
    const blocoDoItem = (item) => {
      // Complemento com classificação escolhida à mão
      let clsId = item?.classificacao_id ?? mapa[item?.tipo_item];
      if (clsId == null) return 'Outros';
      const cls = classePorId[clsId];
      if (!cls) return 'Outros';
      return blocoPorId[cls.bloco_id]?.nome || 'Outros';
    };
    const nomesBlocosOrdenados = [...blocos].sort((a, b) => a.ordem - b.ordem).map(b => b.nome);
    // Opções para o seletor de complemento: "Bloco › Classificação", ordenadas
    const opcoes = [...classes]
      .sort((a, b) => (blocoPorId[a.bloco_id]?.ordem ?? 999) - (blocoPorId[b.bloco_id]?.ordem ?? 999) || a.ordem - b.ordem)
      .map(c => ({ id: c.id, label: `${blocoPorId[c.bloco_id]?.nome || '—'} › ${c.nome}` }));
    return { blocos, classes, mapa, blocoDoItem, ordemBloco, nomesBlocosOrdenados, classePorId, blocoPorId, opcoes };
  }, [classificacoes]);

  // Agrupa itens do orçamento por bloco (nível 1), na ordem definida no banco
  const agruparPorBloco = React.useCallback((itens) => {
    const grupos = {};
    (itens || []).forEach(l => {
      const bloco = classIndex.blocoDoItem(l);
      (grupos[bloco] = grupos[bloco] || []).push(l);
    });
    // ordena as chaves pela ordem do bloco
    return Object.fromEntries(
      Object.entries(grupos).sort(
        ([a], [b]) => (classIndex.ordemBloco[a] ?? 999) - (classIndex.ordemBloco[b] ?? 999)
      )
    );
  }, [classIndex]);

  // ── Checkboxes para aprovar/desmarcar itens ───────────────────────────
  const [materiaisAtivos,     setMateriaisAtivos]     = useState({});
  const [equipamentosAtivos,  setEquipamentosAtivos]  = useState({});
  const [listaAprovada,       setListaAprovada]       = useState(false);

  // ── Embalagem de fluido refrigerante (Card 6) ─────────────────────────
  // Fluido não é vendido a granel — converte o item "Carga de Fluido X kg"
  // numa peça comprável (N cilindros de Y kg). Ver DESIGN_EMBALAGEM_FLUIDO_2026-08-17.md.
  const itemCargaFluidoBruto = (dadosAutomaticos?.materiais || []).find(m => m.tipo_item === 'carga_fluido');
  const infoEmbalagem = React.useMemo(() => {
    if (!itemCargaFluidoBruto) return null;
    const necessario = Number(itemCargaFluidoBruto.quantidade) || 0;
    const doFluido = embalagensFluido
      .filter(e => e.fluido === itemCargaFluidoBruto.fluido)
      .sort((a, b) => a.peso_kg - b.peso_kg);
    if (doFluido.length === 0) return null;
    const suficientes = doFluido.filter(e => e.peso_kg >= necessario);
    return { necessario, opcoes: doFluido, suficientes, maior: doFluido[doFluido.length - 1] };
  }, [itemCargaFluidoBruto?.quantidade, itemCargaFluidoBruto?.fluido, embalagensFluido]);

  // Embalagem escolhida pelo técnico — peso_kg da opção selecionada (entre as suficientes)
  const [embalagemEscolhidaKg, setEmbalagemEscolhidaKg] = useState(null);
  useEffect(() => {
    if (!infoEmbalagem) { setEmbalagemEscolhidaKg(null); return; }
    // Default: a maior entre as opções que cobrem a carga sozinha (comportamento observado em
    // campo — deixar sobra de fluido pra eventual atendimento de garantia)
    if (infoEmbalagem.suficientes.length > 0) {
      setEmbalagemEscolhidaKg(infoEmbalagem.suficientes[infoEmbalagem.suficientes.length - 1].peso_kg);
    } else {
      setEmbalagemEscolhidaKg(null); // sem opção suficiente sozinha — cai pro fallback da maior, sem escolha
    }
  }, [infoEmbalagem?.necessario, infoEmbalagem?.opcoes?.length]);

  // Aplica a embalagem escolhida (ou o fallback de múltiplas unidades da maior) sobre o item
  // "Carga de Fluido" — ponto único de transformação, usado tanto na lista de seleção quanto em
  // tudo que deriva de materiaisAprovados (payload do orçamento, PDF, Excel de cotação).
  const materiaisComEmbalagem = React.useMemo(() => {
    const materiais = dadosAutomaticos?.materiais || [];
    if (!infoEmbalagem) return materiais;
    const usarFallback = infoEmbalagem.suficientes.length === 0;
    const pesoEscolhido = usarFallback ? infoEmbalagem.maior.peso_kg : embalagemEscolhidaKg;
    if (!pesoEscolhido) return materiais;
    const qtdEmbalagens = Math.ceil(infoEmbalagem.necessario / pesoEscolhido);
    return materiais.map(m => {
      if (m.tipo_item !== 'carga_fluido') return m;
      return {
        ...m,
        item: `${m.item} — Cilindro ${pesoEscolhido}kg`,
        quantidade: qtdEmbalagens,
        unidade: 'un',
        detalhe: `${m.detalhe} | Embalagem: ${qtdEmbalagens}× ${fmtQtd(pesoEscolhido)}kg = ${fmtQtd(qtdEmbalagens * pesoEscolhido)}kg`,
      };
    });
  }, [dadosAutomaticos?.materiais, infoEmbalagem, embalagemEscolhidaKg]);

  // ── Complementos livres (sem catálogo) ───────────────────────────────
  // Restaura os complementos salvos com o projeto; senão começa com uma linha em branco
  const [complementos, setComplementos] = useState(
    (initialValues?.complementos?.length ? initialValues.complementos : [novoComplemento()])
  );

  // ── Orçamento e UI ───────────────────────────────────────────────────
  const [orcamento,    setOrcamento]    = useState(null);
  const [erro,         setErro]         = useState(null);
  const [loading,      setLoading]      = useState(false);

  // ── Verificação de cotação ────────────────────────────────────────────
  const [cotacaoAviso,        setCotacaoAviso]        = useState(null); // 'nenhuma' | 'aguardando'
  const [cotacoesEmAndamento, setCotacoesEmAndamento] = useState([]);
  const [cotacoesProcessadas, setCotacoesProcessadas] = useState([]);
  const [modalEscolhaCotacao, setModalEscolhaCotacao] = useState(false);
  const [cotacaoEscolhidaId,  setCotacaoEscolhidaId] = useState(null); // null = melhor preço

  // Assinatura do conteúdo de cada saída no momento em que foi gerada (para sinalizar desatualização)
  const [geradas, setGeradas] = useState({}); // { listaExcel, listaPdf, proposta, cotacao }

  // Rastreabilidade da base de preços: de qual(is) cotação(ões) o orçamento foi gerado
  // { modo: 'unica'|'melhor_preco', cotacoes: [{id, codigo, fornecedor_id, data_recebimento}] }
  const [baseCotacao, setBaseCotacao] = useState(initialValues?.baseCotacao ?? null);
  const [baseDesatualizada, setBaseDesatualizada] = useState(false);
  const [loadingCotacaoCheck, setLoadingCotacaoCheck] = useState(false);
  const [itensSemPreco,       setItensSemPreco]       = useState([]);
  const [precosManuals,       setPrecosManuals]       = useState({}); // norm(desc) → string
  const ultimoPrecoMapRef = useRef(new Map()); // guarda precoMap da última geração
  const [dadosCliente, setDadosCliente] = useState(
    initialValues?.dadosCliente ?? { nome: '', cnpj: '', contato: '', celular: '', email: '' }
  );
  const [clientes,        setClientes]        = useState([]);
  const [clienteSalvoId,  setClienteSalvoId]  = useState(null);
  const [buscaCliente,    setBuscaCliente]    = useState('');
  const [mostrarLista,    setMostrarLista]    = useState(false);
  const [modoNovoCliente, setModoNovoCliente] = useState(false);

  // ── Configurações da proposta ─────────────────────────────────────────
  const iv = initialValues || {};
  const [incluirResumoTecnico,   setIncluirResumoTecnico]   = useState(iv.incluirResumoTecnico ?? true);
  const [modoFaturamento,        setModoFaturamento]        = useState(iv.modoFaturamento ?? 'empreitada'); // 'empreitada' | 'venda_direta'
  const [custos, setCustos] = useState(iv.custos ?? { mo_paineis: '', mo_refrigeracao: '', locomocao: '', despesas: '', outros: '' });
  const [margemMateriais, setMargemMateriais] = useState(iv.margemMateriais ?? 25);
  const [margemServicos,  setMargemServicos]  = useState(iv.margemServicos ?? 25);
  const [imposto,        setImposto]        = useState(iv.imposto ?? 6);
  const [apresentacao,     setApresentacao]     = useState(iv.apresentacao ?? 'blocos'); // 'blocos' | 'global'
  const [exibicaoMateriais, setExibicaoMateriais] = useState(iv.exibicaoMateriais ?? 'itemizado'); // 'itemizado' | 'resumo' | 'sem_preco' (só venda_direta)
  const [listaEmpreitada,   setListaEmpreitada]   = useState(iv.listaEmpreitada ?? 'completa'); // 'completa' | 'totais' (só empreitada)
  const [moSeparada,     setMoSeparada]     = useState(iv.moSeparada ?? false);
  const [resumoObjeto,   setResumoObjeto]   = useState(iv.resumoObjeto ?? 'Fornecimento e instalação de câmara frigorífica completa, conforme dimensionamento técnico.');
  const [cond,           setCond]           = useState(iv.cond ?? CONDICOES_PADRAO);

  // Auto-aprovação quando chamado a partir do PainelCotacoes
  useEffect(() => {
    if (triggerGerarProposta === 0) return;
    if (totalItens > 0) {
      setListaAprovada(true);
      // Pequeno delay para garantir que o DOM renderizou o carrinho antes de verificar
      setTimeout(() => verificarEGerar(), 300);
    }
  }, [triggerGerarProposta]);

  // Reinicia checkboxes quando dadosAutomaticos muda
  useEffect(() => {
    const m = {}; (dadosAutomaticos?.materiais    || []).forEach((_, i) => { m[i] = true; }); setMateriaisAtivos(m);
    const e = {}; (dadosAutomaticos?.equipamentos || []).forEach((_, i) => { e[i] = true; }); setEquipamentosAtivos(e);
    setListaAprovada(false);
    setOrcamento(null);
  }, [dadosAutomaticos]);

  const toggleMaterial    = (i) => setMateriaisAtivos(p => ({ ...p, [i]: !p[i] }));
  const toggleEquipamento = (i) => setEquipamentosAtivos(p => ({ ...p, [i]: !p[i] }));

  const materiaisAprovados    = materiaisComEmbalagem.filter((_, i) => materiaisAtivos[i]);
  const equipamentosAprovados = (dadosAutomaticos?.equipamentos || []).filter((_, i) => equipamentosAtivos[i]);

  // ── Complementos ─────────────────────────────────────────────────────
  const updateComplemento = (i, f, v) => {
    const l = [...complementos]; l[i] = { ...l[i], [f]: v }; setComplementos(l);
  };
  const removerComplemento = (i) => setComplementos(complementos.filter((_, j) => j !== i));
  const complementosPreenchidos = complementos.filter(c => c.descricao.trim());

  const totalItens = materiaisAprovados.length + equipamentosAprovados.length + complementosPreenchidos.length;

  useEffect(() => {
    if (onValoresChange) onValoresChange({
      dadosCliente,
      incluirResumoTecnico,
      modoFaturamento, custos, margemMateriais, margemServicos, imposto,
      apresentacao, exibicaoMateriais, listaEmpreitada, moSeparada, resumoObjeto, cond,
      baseCotacao, complementos,
    });
  }, [dadosCliente, incluirResumoTecnico, modoFaturamento,
      custos, margemMateriais, margemServicos, imposto, apresentacao,
      exibicaoMateriais, listaEmpreitada, moSeparada, resumoObjeto, cond, baseCotacao, complementos]);

  // ── Tabela de peso de tubo de cobre (fallback para projetos sem quantidade_kg) ──
  const [pesosTubo, setPesosTubo] = useState({}); // { "1/2\"": { fina, grossa } }
  useEffect(() => {
    api.get('/api/v1/tubulacao/peso-tubo-cobre')
      .then(r => {
        const m = {};
        (r.data || []).forEach(p => { m[p.bitola_pol] = { fina: p.parede_fina, grossa: p.parede_grossa }; });
        setPesosTubo(m);
      })
      .catch(() => {});
  }, []);

  // Extrai bitola do nome do item: "Tubo Cobre 1/2\" (Líquido)" → "1/2\""
  const extrairBitola = (nomeItem) => {
    const m = (nomeItem || '').match(/Tubo Cobre ([^\s(]+)/);
    return m ? m[1] : null;
  };

  const calcularKg = (item, quantidade, parede) => {
    if (item.quantidade_kg != null) return item.quantidade_kg;
    if (item.peso_por_metro != null) return Math.round(item.peso_por_metro * quantidade * 1000) / 1000;
    const bitola = extrairBitola(item.item);
    if (!bitola || !pesosTubo[bitola]) return null;
    const kgM = parede === 'grossa' ? pesosTubo[bitola].grossa : pesosTubo[bitola].fina;
    return kgM != null ? Math.round(kgM * quantidade * 1000) / 1000 : null;
  };

  // Tubo de cobre é cotado por kg: retorna o peso em kg do material, ou null se não for tubo de cobre
  const kgSeTubo = (m) => {
    if (m.unidade !== 'm') return null;
    const qtd = parseFloat(m.quantidade ?? m.qtd) || 0;
    return calcularKg(m, qtd, m.detalhe?.includes('grossa') ? 'grossa' : 'fina');
  };
  // Texto de quantidade para exibição: tubo de cobre em kg; demais mantêm o padrão original
  const qtdeExibir = (m) => {
    const kg = kgSeTubo(m);
    if (kg != null) return `${fmtQtd(kg)} kg`;
    return m.quantidade != null ? `${fmtQtd(m.quantidade)} ${m.unidade || 'un'}` : (m.qtd ?? '');
  };

  // ── Clientes cadastrados ──────────────────────────────────────────────
  useEffect(() => {
    api.get('/api/v1/clientes').then(r => {
      const lista = r.data || [];
      setClientes(lista);
      // Auto-preenche se o formulário está vazio mas o projeto tem nome de cliente
      const nomeNoProjeto = projetoAtual?.cliente?.trim();
      const formularioVazio = !dadosCliente.nome?.trim();
      if (nomeNoProjeto && formularioVazio) {
        const match = lista.find(c => c.nome.toLowerCase() === nomeNoProjeto.toLowerCase());
        if (match) {
          setDadosCliente({ nome: match.nome, cnpj: match.cnpj || '', contato: match.contato || '', celular: match.celular || '', email: match.email || '' });
          setClienteSalvoId(match.id);
        }
      }
    }).catch(() => {});
  }, []);

  const clientesFiltrados = clientes.filter(c =>
    c.nome.toLowerCase().includes(buscaCliente.toLowerCase()) ||
    (c.cnpj || '').includes(buscaCliente) ||
    (c.email || '').toLowerCase().includes(buscaCliente.toLowerCase())
  );

  const selecionarCliente = (c) => {
    setDadosCliente({ nome: c.nome, cnpj: c.cnpj || '', contato: c.contato || '', celular: c.celular || '', email: c.email || '' });
    setClienteSalvoId(c.id);
    setMostrarLista(false);
    setBuscaCliente('');
    setModoNovoCliente(false);
    if (onClienteChange) onClienteChange(c.nome);
  };

  const salvarCliente = async () => {
    try {
      if (clienteSalvoId) {
        const r = await api.patch(`/api/v1/clientes/${clienteSalvoId}`, dadosCliente);
        setClientes(prev => prev.map(c => c.id === clienteSalvoId ? r.data : c));
      } else {
        const r = await api.post('/api/v1/clientes', dadosCliente);
        setClientes(prev => [...prev, r.data]);
        setClienteSalvoId(r.data.id);
      }
      setModoNovoCliente(false);
      alert('Cliente salvo com sucesso!');
    } catch {
      alert('Erro ao salvar cliente.');
    }
  };

  // ── Dados do cliente ─────────────────────────────────────────────────
  const handleClienteChange = (e) => {
    const { name, value } = e.target;
    setDadosCliente(p => ({ ...p, [name]: value }));
    setClienteSalvoId(null);
    if (name === 'nome' && onClienteChange) onClienteChange(value);
  };

  // ── Gerar orçamento (com mapa de preços opcional) ────────────────────
  const gerarOrcamentoComPrecos = async (precoMap = new Map(), extras = {}) => {
    setLoading(true); setErro(null);
    const semPreco = [];

    // Fase B: preço da própria empresa (lista cadastrada ou última cotação histórica,
    // resolvido pelo backend) preenche o que a cotação deste projeto não cobriu — nunca
    // sobrescreve um preço que já veio de uma cotação escolhida pra este orçamento.
    const mapaCompleto = new Map(precoMap);
    try {
      const { data: mapaEmpresa } = await api.get('/api/v1/produto-empresa/mapa-precos');
      for (const [chave, info] of Object.entries(mapaEmpresa)) {
        if (!mapaCompleto.has(chave)) mapaCompleto.set(chave, info.preco);
      }
    } catch {
      // Sem empresa vinculada ou erro pontual — segue só com o precoMap da cotação
    }

    const buscarPreco = (descricao) => {
      const p = mapaCompleto.get(norm(descricao));
      if (p == null) semPreco.push(descricao);
      return p ?? null;
    };

    const payload = {
      materiais: materiaisAprovados.map(m => {
        const descricao = m.comprimento ? `${m.item} ${m.comprimento}m` : m.item;
        const precoManual = parseFloat(extras[norm(descricao)]) || null;
        // Tubo de cobre é cotado/pago por KG (coluna F). A quantidade do orçamento tem que ser kg,
        // não metros (coluna E) — igual à planilha de cotação (montarItensCotacao).
        const qtd = parseFloat(m.quantidade ?? m.qtd ?? 1) || 1;
        const parede = m.detalhe?.includes('grossa') ? 'grossa' : 'fina';
        const kgTotal = m.unidade === 'm' ? calcularKg(m, qtd, parede) : null;
        return {
          id: m.id,
          item: descricao,
          qtde: kgTotal != null ? kgTotal : qtd,
          detalhe: [m.detalhe || m.descricao, m.area_total ? `${fmtQtd(m.area_total)} m²` : null].filter(Boolean).join(' — '),
          preco_unitario: precoManual ?? buscarPreco(descricao),
          tipo_item: m.tipo_item ?? null,
        };
      }),
      equipamentos: equipamentosAprovados.map(e => {
        const descricao = e.nome || e.item;
        const precoManual = parseFloat(extras[norm(descricao)]) || null;
        return {
          id: e.id, item: descricao,
          qtde: parseFloat(e.qtde ?? 1) || 1,
          detalhe: e.detalhe || '',
          preco_unitario: precoManual ?? buscarPreco(descricao),
          categoria: 'equipamento',
          tipo_item: e.tipo_item ?? null,
        };
      }),
    };

    try {
      const r = await api.post('/api/v1/orcamento', payload);
      setOrcamento(r.data);
      setItensSemPreco(semPreco);
      if (semPreco.length > 0) {
        const init = {};
        semPreco.forEach(d => { init[norm(d)] = ''; });
        setPrecosManuals(init);
      }
      setModalEscolhaCotacao(false);
      setCotacaoAviso(null);
    } catch (err) {
      const detalhe = err?.response?.data?.detail;
      const msg = Array.isArray(detalhe)
        ? detalhe.map(d => `${d.loc?.join('.')}: ${d.msg}`).join(' | ')
        : (typeof detalhe === 'string' ? detalhe : null);
      setErro(msg ? `Erro de validação: ${msg}` : "Erro ao gerar orçamento.");
      console.error('[gerarOrcamento] payload:', payload, 'erro:', err?.response?.data);
    } finally { setLoading(false); }
  };

  // ── Verifica cotação antes de gerar ──────────────────────────────────
  // Descritor da base de preços (qual cotação gerou o orçamento) — para rastreabilidade
  const _metaBase = (lista, modo) => ({
    modo,
    cotacoes: lista.map(c => ({
      id: c.id, codigo: c.codigo, fornecedor_id: c.fornecedor_id, data_recebimento: c.data_recebimento,
    })),
  });

  const verificarEGerar = async () => {
    if (!projetoAtual?.id) return;
    setCotacaoAviso(null); setItensSemPreco([]); setPrecosManuals({});
    setBaseDesatualizada(false);
    setLoadingCotacaoCheck(true);
    try {
      const r = await api.get(`/api/v1/cotacoes?projeto_id=${projetoAtual.id}`);
      const cotacoes = (r.data || []).filter(c => c.status !== 'cancelada');
      const processadas = cotacoes.filter(c => c.status === 'processada');

      if (cotacoes.length === 0) {
        setCotacaoAviso('nenhuma');
      } else if (processadas.length === 0) {
        setCotacoesEmAndamento(cotacoes);
        setCotacaoAviso('aguardando');
      } else if (processadas.length === 1) {
        setCotacaoEscolhidaId(processadas[0].id);
        setBaseCotacao(_metaBase([processadas[0]], 'unica'));
        await _gerarComCotacoes([processadas[0].id]);
      } else {
        setCotacoesProcessadas(processadas);
        setCotacaoEscolhidaId(null);
        setModalEscolhaCotacao(true);
      }
    } catch {
      // Falha ao verificar — gera sem preços da cotação
      await gerarOrcamentoComPrecos();
    } finally {
      setLoadingCotacaoCheck(false);
    }
  };

  const _gerarComCotacoes = async (ids) => {
    const cotacoesData = await Promise.all(ids.map(id => api.get(`/api/v1/cotacoes/${id}`)));
    const precoMap = new Map();
    for (const r of cotacoesData) {
      for (const item of (r.data.itens || [])) {
        if (item.preco_unitario != null && item.preco_unitario > 0) {
          const key = norm(item.descricao);
          if (!precoMap.has(key) || item.preco_unitario < precoMap.get(key)) {
            precoMap.set(key, item.preco_unitario);
          }
        }
      }
    }
    ultimoPrecoMapRef.current = precoMap;
    await gerarOrcamentoComPrecos(precoMap);
  };

  const confirmarEscolhaCotacao = async () => {
    if (cotacaoEscolhidaId === null) {
      // Melhor preço: usa todas as processadas
      setBaseCotacao(_metaBase(cotacoesProcessadas, 'melhor_preco'));
      await _gerarComCotacoes(cotacoesProcessadas.map(c => c.id));
    } else {
      const esc = cotacoesProcessadas.find(c => c.id === cotacaoEscolhidaId);
      if (esc) setBaseCotacao(_metaBase([esc], 'unica'));
      await _gerarComCotacoes([cotacaoEscolhidaId]);
    }
  };

  // Detecta se a base de preços mudou depois de gerado (fornecedor reenviou → data_recebimento muda)
  useEffect(() => {
    if (!orcamento || !baseCotacao?.cotacoes?.length || !projetoAtual?.id) return;
    let cancelado = false;
    (async () => {
      try {
        const r = await api.get(`/api/v1/cotacoes?projeto_id=${projetoAtual.id}`);
        const atuais = new Map((r.data || []).map(c => [c.id, c]));
        const mudou = baseCotacao.cotacoes.some(b => {
          const a = atuais.get(b.id);
          return a && a.data_recebimento !== b.data_recebimento;
        });
        if (!cancelado) setBaseDesatualizada(mudou);
      } catch { /* silencioso */ }
    })();
    return () => { cancelado = true; };
  }, [orcamento, baseCotacao, projetoAtual?.id]);

  // Texto de rastreabilidade da base (uso interno)
  const textoBaseCotacao = () => {
    const cs = baseCotacao?.cotacoes || [];
    if (!cs.length) return null;
    const fmtData = (d) => d ? new Date(d).toLocaleDateString('pt-BR') : 's/ data';
    if (baseCotacao.modo === 'melhor_preco')
      return `Melhor preço entre ${cs.length} cotações — ${cs.map(c => c.codigo).join(', ')}`;
    return `${cs[0].codigo} · recebida ${fmtData(cs[0].data_recebimento)}`;
  };

  const recalcularComPrecosManuals = async () => {
    // Usa o precoMap da última cotação + os preços manuais como override
    await gerarOrcamentoComPrecos(ultimoPrecoMapRef.current, precosManuals);
  };

  // Preço efetivo do complemento: manual (preco_unit) tem prioridade; senão, usa o preço
  // vindo da cotação (precoMap por descrição). Corrige complementos cotados que apareciam "a cotação".
  const precoComplemento = (c) =>
    parseFloat(c.preco_unit) || ultimoPrecoMapRef.current.get(norm(c.descricao)) || 0;

  // ── Total dos complementos ────────────────────────────────────────────
  const totalComplementos = complementosPreenchidos.reduce((s, c) => {
    const q = parseFloat(c.qtde) || 1;
    return s + precoComplemento(c) * q;
  }, 0);

  // ── Sinalização de saídas desatualizadas ──────────────────────────────
  // Lista de materiais e cotação dependem só dos itens; a proposta depende também do financeiro.
  const sigLista = useMemo(() => JSON.stringify({
    eq: equipamentosAprovados.map(e => [e.nome || e.item, e.qtde ?? 1]),
    mat: materiaisAprovados.map(m => [m.item, m.quantidade ?? m.qtd ?? 1, m.comprimento ?? '']),
    comp: complementos.filter(c => c.descricao.trim()).map(c => [c.descricao, c.qtde, c.unidade]),
  }), [equipamentosAprovados, materiaisAprovados, complementos]);

  const sigProposta = useMemo(() => JSON.stringify({
    sigLista, custos, margemMateriais, margemServicos, imposto, modoFaturamento,
    exibicaoMateriais, apresentacao, moSeparada, cond, cliente: dadosCliente,
    precosComp: complementos.map(c => c.preco_unit), temOrc: !!orcamento,
  }), [sigLista, custos, margemMateriais, margemServicos, imposto, modoFaturamento,
       exibicaoMateriais, apresentacao, moSeparada, cond, dadosCliente, complementos, orcamento]);

  const marcarGerada = (tipo) => setGeradas(g => ({ ...g, [tipo]: tipo === 'proposta' ? sigProposta : sigLista }));
  const estaDesatualizada = (tipo) => {
    const s = geradas[tipo];
    return s != null && s !== (tipo === 'proposta' ? sigProposta : sigLista);
  };
  const SeloStale = ({ tipo, texto = '⚠️ desatualizada' }) => estaDesatualizada(tipo) ? (
    <span className="text-[9px] font-bold text-amber-700 bg-amber-100 border border-amber-300 px-1.5 py-0.5 rounded-full whitespace-nowrap animate-pulse">
      {texto}
    </span>
  ) : null;

  const calcFinanceiro = () => {
    const custo_materiais = (orcamento?.custo_total_projeto_rs || 0) + totalComplementos;
    const n = (v) => parseFloat(v) || 0;
    const custo_servicos = n(custos.mo_paineis) + n(custos.mo_refrigeracao) + n(custos.locomocao) + n(custos.despesas) + n(custos.outros);
    const mkFator = (margemPct) => {
      const taxa = (parseFloat(margemPct) || 0) + (parseFloat(imposto) || 0);
      return taxa < 99 ? 1 / (1 - taxa / 100) : 1;
    };
    const fatorMateriais = mkFator(margemMateriais);
    const fatorServicos  = mkFator(margemServicos);
    const fator = fatorServicos; // usado nos blocos de serviço

    let preco_venda, preco_materiais_cliente, preco_servicos_cliente;
    if (modoFaturamento === 'venda_direta') {
      // Fornecedor fatura direto ao cliente: materiais a custo de cotação, sem margem
      preco_servicos_cliente = custo_servicos * fatorServicos;
      preco_materiais_cliente = custo_materiais;
      preco_venda = preco_materiais_cliente + preco_servicos_cliente;
    } else {
      preco_materiais_cliente = custo_materiais * fatorMateriais;
      preco_servicos_cliente = custo_servicos * fatorServicos;
      preco_venda = preco_materiais_cliente + preco_servicos_cliente;
    }

    // Blocos de material para apresentação — classificação via banco (tipo_item → bloco)
    const blocosMatMap = {};
    (orcamento?.detalhamento_itens || []).forEach(l => {
      const bloco = classIndex.blocoDoItem(l);
      blocosMatMap[bloco] = (blocosMatMap[bloco] || 0) + (l.custo_total_rs || 0);
    });
    // Complementos: cada um vai para o bloco da classificação escolhida (default "Outros")
    complementosPreenchidos.forEach(c => {
      const custo = precoComplemento(c) * (parseFloat(c.qtde) || 1);
      if (custo <= 0) return;
      const bloco = classIndex.blocoDoItem({ classificacao_id: c.classificacao_id });
      blocosMatMap[bloco] = (blocosMatMap[bloco] || 0) + custo;
    });
    const blocosCliente = Object.entries(blocosMatMap)
      .sort(([a], [b]) => (classIndex.ordemBloco[a] ?? 999) - (classIndex.ordemBloco[b] ?? 999))
      .map(([nome, custo]) => ({
        nome,
        valor: modoFaturamento === 'venda_direta' ? custo : custo * fatorMateriais,
      }));

    const mo_p = n(custos.mo_paineis), mo_r = n(custos.mo_refrigeracao);
    const overhead = n(custos.locomocao) + n(custos.despesas) + n(custos.outros);
    let blocosServicos;
    // No faturamento direto (exceto resumo global), "Por blocos" já quebra os serviços.
    // No resumo global, quem controla a quebra é apenas o toggle "MO separada".
    const quebrarServicos = moSeparada ||
      (modoFaturamento === 'venda_direta' && exibicaoMateriais !== 'resumo' && apresentacao === 'blocos');
    if (quebrarServicos) {
      blocosServicos = [
        mo_p   > 0 ? { nome: 'Mão de obra — montagem de painéis',                       valor: mo_p   * fator } : null,
        mo_r   > 0 ? { nome: 'Mão de obra — montagem de refrigeração e comissionamento', valor: mo_r   * fator } : null,
        overhead > 0 ? { nome: 'Deslocamento, despesas e outros',                        valor: overhead * fator } : null,
      ].filter(Boolean);
      if (blocosServicos.length === 0)
        blocosServicos = [{ nome: 'Instalação, mobilização e comissionamento', valor: preco_servicos_cliente }];
    } else {
      blocosServicos = [{ nome: 'Instalação, mobilização e comissionamento', valor: preco_servicos_cliente }];
    }
    const blocosMateriais = [...blocosCliente];
    blocosCliente.push(...blocosServicos);

    const custo_total = custo_materiais + custo_servicos;
    const faturamento_proprio = modoFaturamento === 'venda_direta' ? preco_servicos_cliente : preco_venda;
    const custo_proprio = modoFaturamento === 'venda_direta' ? custo_servicos : custo_total;
    const impostos_valor = faturamento_proprio * ((parseFloat(imposto) || 0) / 100);
    const lucro_liquido = faturamento_proprio - custo_proprio - impostos_valor;

    return { custo_materiais, custo_servicos, custo_total, preco_venda, preco_materiais_cliente, preco_servicos_cliente, faturamento_proprio, impostos_valor, lucro_liquido, blocosCliente, blocosServicos, blocosMateriais, fatorMateriais };
  };

  const cf = calcFinanceiro();
  const totalGeral = cf.preco_venda;

  // ── PDF ───────────────────────────────────────────────────────────────
  const gerarPDFCanvas = async () => {
    if (!propostaRef.current) return;
    setLoading(true);
    try {
      const canvas = await html2canvas(propostaRef.current, { scale: 2, useCORS: true, logging: false });
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pw = pdf.internal.pageSize.getWidth();
      const ph = pdf.internal.pageSize.getHeight();
      const ch = (canvas.height * pw) / canvas.width;
      let left = ch, pos = 0;
      pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, pos, pw, ch);
      left -= ph;
      while (left >= 0) { pos = left - ch; pdf.addPage(); pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, pos, pw, ch); left -= ph; }
      pdf.save(`Orcamento_${dadosCliente.nome?.replace(/\s+/g, '_') || 'Camara'}.pdf`);
    } catch { setErro("Erro ao gerar PDF."); }
    finally { setLoading(false); }
  };

  const gerarPDF = () => {
    setLoading(true);
    try {
      const pdf = new jsPDF('p', 'mm', 'a4');
      const PW = 210, PH = 297, ML = 14, MR = 196, CW = MR - ML;
      let y = 0;

      const novaP = () => { pdf.addPage(); y = 14; };
      const checar = (h = 10) => { if (y + h > PH - 14) novaP(); };

      const txt = (t, x, yy, opts = {}) => pdf.text(String(t ?? ''), x, yy, opts);
      const wrap = (t, x, yy, maxW) => { const ls = pdf.splitTextToSize(String(t ?? ''), maxW); pdf.text(ls, x, yy); return ls.length; };

      // ── Cabeçalho ──────────────────────────────────────────────────────
      pdf.setFillColor(15, 23, 42);
      pdf.rect(0, 0, PW, 38, 'F');
      pdf.setTextColor(255, 255, 255);
      pdf.setFontSize(7); pdf.setFont('helvetica', 'bold');
      txt('PROPOSTA TÉCNICA COMERCIAL', ML, 10);
      pdf.setFontSize(18); pdf.setFont('helvetica', 'bold');
      txt(dadosCliente.nome || 'Cliente não informado', ML, 20);
      pdf.setFontSize(8); pdf.setFont('helvetica', 'normal');
      const objLines = pdf.splitTextToSize(resumoObjeto || '', CW - 40);
      pdf.text(objLines, ML, 27);

      pdf.setFontSize(7); pdf.setFont('helvetica', 'bold');
      txt('EMISSÃO', MR - 30, 10, { align: 'right' });
      txt('VALIDADE', MR, 10, { align: 'right' });
      pdf.setFont('helvetica', 'normal'); pdf.setFontSize(8);
      txt(new Date().toLocaleDateString('pt-BR'), MR - 30, 15, { align: 'right' });
      const valData = new Date(Date.now() + (parseInt(cond.validade_dias) || 10) * 86400000).toLocaleDateString('pt-BR');
      txt(valData, MR, 15, { align: 'right' });
      pdf.setTextColor(0, 0, 0);
      y = 46;

      // ── Dados do cliente ──────────────────────────────────────────────
      pdf.setFillColor(248, 250, 252);
      pdf.rect(ML, y - 4, CW, 22, 'F');
      pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100);
      txt('INFORMAÇÕES DO CLIENTE', ML + 2, y); pdf.setTextColor(0);
      pdf.setFontSize(10); pdf.setFont('helvetica', 'bold');
      txt(dadosCliente.nome || '---', ML + 2, y + 5);
      pdf.setFontSize(8); pdf.setFont('helvetica', 'normal');
      if (dadosCliente.cnpj) txt(`CNPJ/CPF: ${dadosCliente.cnpj}`, ML + 2, y + 10);
      const metade = ML + CW / 2;
      pdf.setFontSize(7); pdf.setTextColor(100); txt('CONTATO', metade, y); txt('CELULAR', metade + 40, y);
      pdf.setTextColor(0); pdf.setFontSize(8); pdf.setFont('helvetica', 'bold');
      txt(dadosCliente.contato || '---', metade, y + 5);
      txt(dadosCliente.celular || '---', metade + 40, y + 5);
      // E-mail em linha própria (rótulo + valor na mesma linha) — evita estourar a margem direita
      pdf.setFontSize(7); pdf.setFont('helvetica', 'normal'); pdf.setTextColor(100); txt('E-MAIL', metade, y + 10);
      pdf.setFontSize(8); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(0); txt(dadosCliente.email || '---', metade + 14, y + 10);
      y += 28;

      // ── Resumo técnico ────────────────────────────────────────────────
      if (incluirResumoTecnico && resumoTecnico) {
        checar(30);
        pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100);
        txt('ESPECIFICAÇÕES TÉCNICAS', ML, y); pdf.setTextColor(0); y += 4;
        const specs = [
          ['Comprimento', `${fmtQtd(resumoTecnico.comprimento)} m`],
          ['Largura', `${fmtQtd(resumoTecnico.largura)} m`],
          ['Altura', `${fmtQtd(resumoTecnico.altura)} m`],
          ['T. Interna', `${fmtQtd(resumoTecnico.temperatura_interna)} °C`],
          ['Isolamento', `${resumoTecnico.nucleo} ${resumoTecnico.espessura}mm`],
        ].filter(Boolean);
        const colW = CW / specs.length;
        specs.forEach((s, i) => {
          const x = ML + i * colW;
          pdf.setFillColor(241, 245, 249); pdf.rect(x, y, colW - 2, 12, 'F');
          pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100);
          txt(s[0].toUpperCase(), x + 2, y + 4);
          pdf.setFontSize(9); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(0);
          txt(s[1], x + 2, y + 10);
        });
        y += 18;

        // Carga térmica em destaque + produto / movimentação / temperatura de entrada
        if (resumoTecnico.carga_termica) {
          checar(22);
          pdf.setFillColor(236, 253, 245); pdf.rect(ML, y, CW, 16, 'F');
          pdf.setDrawColor(167, 243, 208); pdf.setLineWidth(0.3); pdf.rect(ML, y, CW, 16); pdf.setLineWidth(0.2);
          pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(5, 150, 105);
          txt('CARGA TÉRMICA CALCULADA', ML + 3, y + 5);
          pdf.setFontSize(14); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(6, 95, 70);
          txt(`${Number(resumoTecnico.carga_termica).toLocaleString('pt-BR')} kcal/h`, ML + 3, y + 12);
          const dets = [
            resumoTecnico.produto ? ['Produto', String(resumoTecnico.produto)] : null,
            (resumoTecnico.movimentacao != null && resumoTecnico.movimentacao !== '' && Number(resumoTecnico.movimentacao) > 0) ? ['Movimentação', `${fmtQtd(resumoTecnico.movimentacao)} kg/dia`] : null,
            (resumoTecnico.temp_entrada != null && resumoTecnico.temp_entrada !== '') ? ['Temp. Entrada', `${fmtQtd(resumoTecnico.temp_entrada)} °C`] : null,
          ].filter(Boolean);
          const detStartX = ML + CW * 0.42;
          const detW = (CW * 0.58) / Math.max(1, dets.length);
          dets.forEach((d, i) => {
            const dx = detStartX + i * detW;
            pdf.setFontSize(5); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(150);
            txt(d[0].toUpperCase(), dx, y + 5);
            pdf.setFontSize(8); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(30);
            txt(d[1], dx, y + 11);
          });
          pdf.setTextColor(0); pdf.setDrawColor(200);
          y += 20;
        }
      }

      // ── Planta técnica da câmara ─────────────────────────────────────
      if (dadosAutomaticos?.imagem_projeto) {
        checar(80);
        pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100);
        txt('PLANTA TÉCNICA DA CÂMARA FRIGORÍFICA', ML, y); pdf.setTextColor(0); y += 4;
        const imgW = CW * 0.6;
        const imgX = ML + (CW - imgW) / 2;
        pdf.addImage(dadosAutomaticos.imagem_projeto, 'PNG', imgX, y, imgW, 65);
        y += 70;
      }

      // ── Escopo ────────────────────────────────────────────────────────
      if (cond.incluso || cond.nao_incluso) {
        checar(20);
        const half = CW / 2 - 2;
        if (cond.incluso) {
          pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(34, 197, 94);
          txt('✓ ESTÁ INCLUÍDO', ML, y); pdf.setTextColor(0);
          pdf.setFontSize(7); pdf.setFont('helvetica', 'normal');
          const nl = wrap(cond.incluso, ML, y + 4, half);
          if (cond.nao_incluso) {
            pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(220, 38, 38);
            txt('✗ NÃO INCLUÍDO', ML + half + 4, y); pdf.setTextColor(0);
            pdf.setFontSize(7); pdf.setFont('helvetica', 'normal');
            wrap(cond.nao_incluso, ML + half + 4, y + 4, half);
          }
          y += nl * 3.5 + 10;
        }
      }

      // ── Lista de itens ────────────────────────────────────────────────
      {
        // Lista omitida no resumo global do fat. direto e no "somente totais" da empreitada;
        // na empreitada os itens saem com preço de venda (markup), nunca com custo
        const modoResumo = (modoFaturamento === 'venda_direta' && exibicaoMateriais === 'resumo')
          || (modoFaturamento === 'empreitada' && listaEmpreitada === 'totais');
        if (!modoResumo) {
        if (modoFaturamento === 'venda_direta' && exibicaoMateriais === 'itemizado') {
          checar(10);
          pdf.setFontSize(7); pdf.setFont('helvetica', 'italic'); pdf.setTextColor(150, 100, 20);
          wrap('Faturamento direto: os materiais e equipamentos abaixo serão faturados diretamente pelo fornecedor ao cliente, pelos valores de cotação, sem margem.', ML, y, CW);
          pdf.setTextColor(0); y += 9;
        }
        const grupos = Object.entries(agruparPorBloco(orcamento.detalhamento_itens)).filter(([, it]) => it.length > 0);
        grupos.forEach(([cat, itens]) => {
          checar(14);
          const rgbCat = corDoBloco(cat).rgb;
          pdf.setDrawColor(...rgbCat); pdf.setLineWidth(0.6); pdf.line(ML, y, MR, y); pdf.setLineWidth(0.2); y += 4;
          pdf.setFillColor(...rgbCat); pdf.rect(ML, y - 2.1, 2.2, 2.2, 'F');
          pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(...rgbCat);
          txt(cat.toUpperCase(), ML + 4, y); pdf.setTextColor(0); y += 5;
          itens.forEach(l => {
            checar(8);
            pdf.setFontSize(8); pdf.setFont('helvetica', 'bold');
            const nL = pdf.splitTextToSize(l.item, CW - 55);
            pdf.text(nL, ML, y);
            pdf.setFont('helvetica', 'normal'); pdf.setTextColor(100);
            pdf.setFontSize(6);
            if (l.detalhe) { checar(4); pdf.text(pdf.splitTextToSize(l.detalhe, CW - 55), ML, y + nL.length * 4); }
            pdf.setFontSize(8); pdf.setTextColor(0);
            txt(`${fmtQtd(l.quantidade)} ${l.unidade}`, MR - 25, y, { align: 'right' });
            if (modoFaturamento === 'venda_direta') {
              if (exibicaoMateriais === 'itemizado') {
                pdf.setFont('helvetica', 'bold');
                txt(`R$ ${fmt(l.custo_total_rs ?? 0)}`, MR, y, { align: 'right' });
              }
            } else {
              pdf.setFont('helvetica', 'bold');
              txt(`R$ ${fmt((l.custo_total_rs ?? 0) * cf.fatorMateriais)}`, MR, y, { align: 'right' });
            }
            y += (nL.length + (l.detalhe ? 1 : 0)) * 4 + 2;
          });
          y += 3;
        });
        }

        if (complementosPreenchidos.length > 0) {
          checar(14);
          pdf.setDrawColor(200); pdf.line(ML, y, MR, y); y += 4;
          pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100);
          txt('COMPLEMENTOS E MATERIAIS ADICIONAIS', ML, y); pdf.setTextColor(0); y += 5;
          complementosPreenchidos.forEach(c => {
            checar(7);
            const pc = precoComplemento(c);
            pdf.setFontSize(8); pdf.setFont('helvetica', 'bold');
            txt(c.descricao, ML, y);
            txt(`${fmtQtd(c.qtde)} ${c.unidade}`, MR - 25, y, { align: 'right' });
            if (modoFaturamento === 'venda_direta' && exibicaoMateriais === 'sem_preco') { /* sem valor */ }
            else if (pc > 0) { pdf.setFont('helvetica', 'bold'); txt(`R$ ${fmt(pc * (parseFloat(c.qtde) || 1) * (modoFaturamento === 'empreitada' ? cf.fatorMateriais : 1))}`, MR, y, { align: 'right' }); }
            else { pdf.setFont('helvetica', 'italic'); pdf.setTextColor(150); txt('A cotação', MR, y, { align: 'right' }); pdf.setTextColor(0); }
            y += 6;
          });
        }
      }

      // ── Investimento ──────────────────────────────────────────────────
      checar(20);
      pdf.setDrawColor(200); pdf.line(ML, y, MR, y); y += 4;
      pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100);
      txt('INVESTIMENTO', ML, y); pdf.setTextColor(0); y += 5;

      const linhaInv = (nome, valor, nota, rgbCor) => {
        checar(nota ? 10 : 7);
        pdf.setFontSize(9); pdf.setFont('helvetica', 'normal');
        if (rgbCor) {
          pdf.setFillColor(...rgbCor); pdf.rect(ML, y - 2.6, 2, 2, 'F');
          pdf.setTextColor(...rgbCor); txt(nome, ML + 3.5, y); pdf.setTextColor(0);
        } else {
          txt(nome, ML, y);
        }
        pdf.setFont('helvetica', 'bold'); txt(`R$ ${fmt(valor)}`, MR, y, { align: 'right' });
        if (nota) { pdf.setFontSize(6); pdf.setFont('helvetica', 'italic'); pdf.setTextColor(150); txt(nota, ML, y + 3.5); pdf.setTextColor(0); y += 3.5; }
        y += 6;
      };
      if (modoFaturamento === 'venda_direta') {
        if (exibicaoMateriais === 'resumo') {
          linhaInv('Cj. materiais de refrigeração e isolamento', cf.custo_materiais, 'Faturamento direto ao fornecedor');
        } else if (exibicaoMateriais === 'itemizado') {
          cf.blocosMateriais.forEach(b => linhaInv(b.nome, b.valor, 'Faturamento direto ao fornecedor — valor de cotação', corDoBloco(b.nome).rgb));
        }
        if (exibicaoMateriais === 'resumo' || apresentacao === 'blocos') {
          cf.blocosServicos.forEach(b => linhaInv(b.nome, b.valor, null, COR_MAO_DE_OBRA.rgb));
        } else {
          linhaInv('Instalação, mobilização e comissionamento', cf.preco_servicos_cliente, null, COR_MAO_DE_OBRA.rgb);
        }
      } else if (apresentacao === 'blocos') {
        cf.blocosCliente.forEach(b => linhaInv(b.nome, b.valor));
      } else {
        checar(12);
        pdf.setFillColor(241, 245, 249); pdf.rect(ML, y - 3, CW, 12, 'F');
        pdf.setFontSize(10); pdf.setFont('helvetica', 'bold');
        txt('Fornecimento e instalação completos', ML + 3, y + 4);
        txt(`R$ ${fmt(modoFaturamento === 'venda_direta' ? cf.preco_servicos_cliente : cf.preco_venda)}`, MR - 2, y + 4, { align: 'right' });
        y += 16;
      }

      // ── Total geral ───────────────────────────────────────────────────
      checar(18);
      pdf.setDrawColor(15, 23, 42); pdf.setLineWidth(0.8); pdf.line(ML, y, MR, y); pdf.setLineWidth(0.2);
      y += 6;
      pdf.setFontSize(8); pdf.setFont('helvetica', 'normal'); pdf.setTextColor(100);
      const notaTotal = modoFaturamento === 'venda_direta'
        ? (exibicaoMateriais === 'sem_preco'
            ? '* Materiais faturados diretamente pelo fornecedor. Valor refere-se aos serviços.'
            : '* Materiais faturados diretamente pelo fornecedor ao cliente, pelos valores de cotação, sem margem. Serviços faturados pelo instalador.')
        : `* Proposta válida até ${valData}. Preços sujeitos a alteração após este prazo.`;
      wrap(notaTotal, ML, y, CW - 50);
      pdf.setFontSize(10); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100);
      txt('INVESTIMENTO TOTAL', MR, y, { align: 'right' });
      pdf.setFontSize(16); pdf.setTextColor(67, 56, 202);
      txt(`R$ ${fmt(modoFaturamento === 'venda_direta' && exibicaoMateriais === 'sem_preco' ? cf.preco_servicos_cliente : cf.preco_venda)}`, MR, y + 8, { align: 'right' });
      pdf.setTextColor(0); y += 20;

      // ── Condições comerciais + Aceite — sempre numa página nova ─────
      novaP();
      pdf.setDrawColor(200); pdf.line(ML, y, MR, y); y += 4;
      pdf.setFillColor(248, 250, 252); pdf.rect(ML, y - 1, CW, 4, 'F');
      pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100);
      txt('CONDIÇÕES COMERCIAIS', ML + 2, y + 2); pdf.setTextColor(0); y += 7;
      const conds = [
        ['Condições de Pagamento', cond.pagamento],
        ['Prazo de Execução', cond.prazo_execucao],
        ['Garantia', cond.garantia],
        ['Validade da Proposta', `${cond.validade_dias} dias úteis a partir da emissão`],
      ].filter(r => r[1]);
      conds.forEach(([label, val]) => {
        const ls = pdf.splitTextToSize(val, CW / 2 - 4);
        checar(ls.length * 3.5 + 8);
        pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100); txt(label.toUpperCase(), ML, y);
        pdf.setFontSize(7); pdf.setFont('helvetica', 'normal'); pdf.setTextColor(0); pdf.text(ls, ML, y + 4);
        y += ls.length * 3.5 + 7;
      });

      // ── Aceite ────────────────────────────────────────────────────────
      checar(28);
      pdf.setDrawColor(200); pdf.line(ML, y, MR, y); y += 10;
      pdf.setFontSize(6); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(100);
      txt('APROVAÇÃO E ACEITE', ML, y); pdf.setTextColor(0); y += 10;
      const halfAce = CW / 2 - 5;
      pdf.setDrawColor(0); pdf.line(ML, y, ML + halfAce, y);
      pdf.line(MR - halfAce, y, MR, y);
      pdf.setFontSize(7); pdf.setFont('helvetica', 'bold');
      txt(dadosCliente.nome || 'Cliente', ML, y + 4);
      txt('Prestador de Serviços', MR - halfAce, y + 4);
      pdf.setFontSize(6); pdf.setFont('helvetica', 'normal'); pdf.setTextColor(100);
      txt('Aprovação do cliente', ML, y + 8);
      txt('Data: _____ / _____ / _________', MR - halfAce, y + 8);

      pdf.save(`Proposta_${(dadosCliente.nome || 'Camara').replace(/\s+/g, '_')}.pdf`);
      marcarGerada('proposta');
    } catch (e) { console.error(e); setErro('Erro ao gerar PDF.'); }
    finally { setLoading(false); }
  };

  // ── Exportar Lista de Engenharia (PDF / Excel) ────────────────────────
  // Cores no mesmo padrão da planilha de cotação (backend/app/services/cotacao_excel.py)
  const COR_HEADER = 'FF1E3A5F';       // navy do cabeçalho
  const COR_PREENCHER = 'FFFFFACD';    // amarelo — colunas para preenchimento manual
  const COR_EQUIP = 'FFEBF5FB';        // azul claro — linhas de equipamento
  const COR_MATERIAL = 'FFFDFEFE';     // quase branco — demais linhas
  const COR_RODAPE = 'FFF4F6F6';       // cinza claro — nota de rodapé
  const BORDA_FINA = { style: 'thin', color: { argb: 'FFCCCCCC' } };

  const _montarLinhasLista = () => {
    const linhas = [];
    equipamentosAprovados.forEach(e => {
      linhas.push({ codigo: e.id ?? '', item: e.nome || e.item, detalhe: e.detalhe || '', qtde: e.qtde ?? 1, unidade: 'un', tipo: 'Equipamento' });
    });
    materiaisAprovados.forEach(m => {
      const kg = kgSeTubo(m);  // tubo de cobre em kg (cotado por kg)
      linhas.push({
        codigo: m.id ?? '',
        item: m.item, detalhe: m.detalhe || m.descricao || '',
        qtde: kg != null ? kg : (m.quantidade ?? m.qtd ?? 1),
        unidade: kg != null ? 'kg' : (m.unidade || (m.comprimento ? 'm' : 'un')),
        tipo: 'Material',
      });
    });
    complementos.filter(c => c.descricao).forEach(c => {
      linhas.push({ codigo: '', item: c.descricao, detalhe: '', qtde: c.qtde || 1, unidade: c.unidade || 'un', tipo: 'Complemento' });
    });
    return linhas;
  };

  // Garante que o projeto está salvo antes de exportar — se ainda não foi salvo,
  // dispara o mesmo fluxo do botão "Salvar" (que pede o nome) e só segue se der certo.
  const garantirProjetoSalvo = async () => {
    if (projetoSalvo) return projetoAtual?.nome || 'Projeto';
    if (!onSalvarProjeto) {
      setErro('Salve o projeto antes de exportar a Lista de Engenharia — o nome do projeto é usado no cabeçalho.');
      return null;
    }
    const salvo = await onSalvarProjeto();
    return salvo?.id ? salvo.nome : null;
  };

  const exportarListaExcel = async () => {
    const nome = await garantirProjetoSalvo();
    if (!nome) return;
    const linhas = _montarLinhasLista();
    const cliente = dadosCliente?.nome?.trim() || '';

    const wb = new ExcelJS.Workbook();
    const ws = wb.addWorksheet('Lista de Engenharia', { properties: { defaultRowHeight: 18 } });
    ws.views = [{ showGridLines: false }];

    const larguras = [10, 14, 30, 32, 9, 8, 14, 20, 26];
    ws.columns = larguras.map(w => ({ width: w }));
    const NCOL = larguras.length; // A..I

    const preencherLinha = (rowIdx, cor, negrito = false, tamanho = 11) => {
      const row = ws.getRow(rowIdx);
      for (let c = 1; c <= NCOL; c++) {
        const cell = row.getCell(c);
        cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: cor } };
        cell.font = { name: 'Arial', bold: negrito, size: tamanho, color: { argb: cor === COR_HEADER ? 'FFFFFFFF' : 'FF1E293B' } };
      }
      return row;
    };

    // Linha 1 — título
    ws.mergeCells(1, 1, 1, NCOL);
    preencherLinha(1, COR_HEADER, true, 14).getCell(1).value = 'LISTA DE ENGENHARIA — MATERIAIS E EQUIPAMENTOS';
    ws.getRow(1).getCell(1).alignment = { vertical: 'middle', horizontal: 'left' };
    ws.getRow(1).height = 24;

    // Linha 2 — projeto / cliente / data
    ws.mergeCells(2, 1, 2, NCOL);
    const linha2 = preencherLinha(2, 'FFEAF2FF', false, 10);
    const dataEmissao = new Date().toLocaleDateString('pt-BR');
    linha2.getCell(1).value = `Projeto: ${nome}` + (cliente ? `   |   Cliente: ${cliente}` : '') + `   |   Emitido em: ${dataEmissao}`;
    linha2.getCell(1).font = { name: 'Arial', italic: true, size: 10, color: { argb: 'FF1E293B' } };

    // Linha 3 — instrução de preenchimento
    ws.mergeCells(3, 1, 3, NCOL);
    const linha3 = preencherLinha(3, COR_PREENCHER, false, 9);
    linha3.getCell(1).value = 'Preencha manualmente as colunas em amarelo (Valor Unit., Fabricante, Observação) — uso interno de engenharia, não é uma cotação com fornecedor.';
    linha3.getCell(1).font = { name: 'Arial', italic: true, size: 9, color: { argb: 'FF7A6900' } };

    // Linha 4 — cabeçalhos de coluna
    const headers = ['Código', 'Tipo', 'Item', 'Detalhe', 'Qtde', 'Un', 'Valor Unit. (R$)', 'Fabricante', 'Observação'];
    const colsEditaveis = new Set([7, 8, 9]); // Valor, Fabricante, Observação
    const linha4 = ws.getRow(4);
    headers.forEach((h, i) => {
      const cell = linha4.getCell(i + 1);
      cell.value = h;
      const cor = colsEditaveis.has(i + 1) ? COR_PREENCHER : COR_HEADER;
      cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: cor } };
      cell.font = { name: 'Arial', bold: true, size: 10, color: { argb: colsEditaveis.has(i + 1) ? 'FF7A6900' : 'FFFFFFFF' } };
      cell.alignment = { vertical: 'middle', horizontal: 'center', wrapText: true };
      cell.border = { top: BORDA_FINA, bottom: BORDA_FINA, left: BORDA_FINA, right: BORDA_FINA };
    });
    linha4.height = 26;

    // Corpo
    const primeiraLinhaItem = 5;
    linhas.forEach((l, idx) => {
      const rowIdx = primeiraLinhaItem + idx;
      const row = ws.getRow(rowIdx);
      const cor = l.tipo === 'Equipamento' ? COR_EQUIP : COR_MATERIAL;
      const valores = [l.codigo, l.tipo, l.item, l.detalhe, l.qtde, l.unidade, null, null, null];
      valores.forEach((v, i) => {
        const cell = row.getCell(i + 1);
        if (v !== null) cell.value = v;
        const editavel = colsEditaveis.has(i + 1);
        cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: editavel ? COR_PREENCHER : cor } };
        cell.font = { name: 'Arial', size: 10 };
        cell.alignment = { vertical: 'middle', horizontal: [5, 7].includes(i + 1) ? 'right' : 'left', wrapText: true };
        cell.border = { top: BORDA_FINA, bottom: BORDA_FINA, left: BORDA_FINA, right: BORDA_FINA };
      });
      row.getCell(7).numFmt = 'R$ #,##0.00';
    });

    // Rodapé
    const ultimaLinhaItem = primeiraLinhaItem + linhas.length - 1;
    const rodapeIdx = ultimaLinhaItem + 2;
    ws.mergeCells(rodapeIdx, 1, rodapeIdx, NCOL);
    const rodape = preencherLinha(rodapeIdx, COR_RODAPE, false, 8);
    rodape.getCell(1).value = 'Lista gerada automaticamente pelo IceNexus a partir do dimensionamento do projeto — não constitui cotação nem orçamento fechado.';
    rodape.getCell(1).font = { name: 'Arial', italic: true, size: 8, color: { argb: 'FF64748B' } };

    ws.views = [{ showGridLines: false, state: 'frozen', ySplit: primeiraLinhaItem - 1 }];

    const buffer = await wb.xlsx.writeBuffer();
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `Lista_Engenharia_${nome.replace(/\s+/g, '_')}.xlsx`;
    a.click(); URL.revokeObjectURL(url);
    marcarGerada('listaExcel');
  };

  const exportarListaPDF = async () => {
    const nome = await garantirProjetoSalvo();
    if (!nome) return;
    const linhas = _montarLinhasLista();
    const cliente = dadosCliente?.nome?.trim() || '';

    const pdf = new jsPDF('l', 'mm', 'a4'); // paisagem — mais colunas
    const pw = pdf.internal.pageSize.getWidth();
    const ph = pdf.internal.pageSize.getHeight();
    const ML = 14, MR = pw - 14;

    // Faixa superior escura
    pdf.setFillColor(30, 58, 95);
    pdf.rect(0, 0, pw, 22, 'F');
    pdf.setTextColor(255, 255, 255);
    pdf.setFontSize(8); pdf.setFont('helvetica', 'bold');
    pdf.text('LISTA DE ENGENHARIA', ML, 9);
    pdf.setFontSize(14);
    pdf.text(nome, ML, 17);
    pdf.setFontSize(8); pdf.setFont('helvetica', 'normal');
    const dataEmissao = new Date().toLocaleDateString('pt-BR');
    pdf.text(`Emitido em: ${dataEmissao}`, MR, 9, { align: 'right' });
    if (cliente) pdf.text(`Cliente: ${cliente}`, MR, 17, { align: 'right' });
    pdf.setTextColor(0, 0, 0);

    // Nota de instrução
    let y = 29;
    pdf.setFillColor(255, 250, 205);
    pdf.rect(ML, y - 4, MR - ML, 6, 'F');
    pdf.setFontSize(7.5); pdf.setFont('helvetica', 'italic'); pdf.setTextColor(122, 105, 0);
    pdf.text('Preencha manualmente Valor Unit., Fabricante e Observação — uso interno de engenharia, não é uma cotação com fornecedor.', ML + 1, y);
    pdf.setTextColor(0, 0, 0);
    y += 8;

    // Colunas da tabela (soma = MR-ML)
    const cols = [
      { label: 'Código', w: 16, align: 'left' },
      { label: 'Tipo', w: 22, align: 'left' },
      { label: 'Item', w: 48, align: 'left' },
      { label: 'Detalhe', w: 50, align: 'left' },
      { label: 'Qtde', w: 14, align: 'right' },
      { label: 'Un', w: 10, align: 'center' },
      { label: 'Valor Unit. (R$)', w: 24, align: 'right' },
      { label: 'Fabricante', w: 30, align: 'left' },
      { label: 'Observação', w: 55, align: 'left' },
    ];
    const editaveis = new Set(['Valor Unit. (R$)', 'Fabricante', 'Observação']);
    const colX = [ML];
    cols.forEach((c, i) => { if (i > 0) colX.push(colX[i - 1] + cols[i - 1].w); });

    const desenharCabecalho = () => {
      pdf.setFontSize(7.5); pdf.setFont('helvetica', 'bold');
      cols.forEach((c, i) => {
        const editavel = editaveis.has(c.label);
        pdf.setFillColor(...(editavel ? [255, 250, 205] : [30, 58, 95]));
        pdf.rect(colX[i], y - 4.5, c.w, 7, 'F');
        pdf.setTextColor(...(editavel ? [122, 105, 0] : [255, 255, 255]));
        const tx = c.align === 'right' ? colX[i] + c.w - 1 : c.align === 'center' ? colX[i] + c.w / 2 : colX[i] + 1;
        pdf.text(c.label, tx, y, { align: c.align === 'left' ? 'left' : c.align });
      });
      pdf.setTextColor(0, 0, 0);
      y += 5;
    };

    desenharCabecalho();
    pdf.setFont('helvetica', 'normal'); pdf.setFontSize(7.5);

    linhas.forEach(l => {
      const linhasItem = pdf.splitTextToSize(l.item || '', cols[2].w - 2);
      const linhasDetalhe = pdf.splitTextToSize(l.detalhe || '', cols[3].w - 2);
      const nLinhas = Math.max(linhasItem.length, linhasDetalhe.length, 1);
      const rowH = Math.max(nLinhas * 3.6 + 2, 6.5);

      if (y + rowH > ph - 12) { pdf.addPage(); y = 16; desenharCabecalho(); pdf.setFont('helvetica', 'normal'); pdf.setFontSize(7.5); }

      const valores = [String(l.codigo ?? ''), l.tipo, linhasItem, linhasDetalhe, String(l.qtde), l.unidade, '', '', ''];
      cols.forEach((c, i) => {
        pdf.setDrawColor(204, 204, 204);
        pdf.setFillColor(...(editaveis.has(c.label) ? [255, 250, 205] : [255, 255, 255]));
        pdf.rect(colX[i], y - 4, c.w, rowH, 'FD');
        const v = valores[i];
        const tx = c.align === 'right' ? colX[i] + c.w - 1 : c.align === 'center' ? colX[i] + c.w / 2 : colX[i] + 1;
        pdf.text(v, tx, y, { align: c.align === 'left' ? 'left' : c.align });
      });
      y += rowH;
    });

    pdf.setFontSize(7); pdf.setFont('helvetica', 'italic'); pdf.setTextColor(100);
    pdf.text('Lista gerada automaticamente pelo IceNexus a partir do dimensionamento do projeto — não constitui cotação nem orçamento fechado.', ML, ph - 6);

    pdf.save(`Lista_Engenharia_${nome.replace(/\s+/g, '_')}.pdf`);
    marcarGerada('listaPdf');
  };

  // ── Cotação com fornecedor (Fase 1) ───────────────────────────────────
  const [modalCotacaoAberto, setModalCotacaoAberto] = useState(false);

  const montarItensCotacao = () => [
    ...equipamentosAprovados.map(e => ({
      tipo_item: e.categoria || 'Equipamento',   // ex: "Unidade Condensadora", "Evaporadora"
      ref_id:    e.id || null,
      descricao: e.nome || e.item,
      detalhe:   e.detalhe || '',
      qtde:      e.qtde || 1,
      unidade:   'un',
    })),
    ...materiaisAprovados.map(m => {
      // Extrai número do campo quantidade — pode vir como int, float ou string "24.50 m²"
      const rawQtd = m.quantidade ?? m.qtd;
      const qtdNum = parseFloat(String(rawQtd));
      const qtd    = isNaN(qtdNum) ? 1 : qtdNum;

      // Para materiais_extras do gabinete (qtd é string), inclui o texto original no detalhe
      const detalheQtd = (typeof rawQtd === 'string' && isNaN(parseFloat(rawQtd)))
        ? rawQtd : null;

      // Tubos de cobre: unidade comercial é kg, metros ficam em qtde_metros
      // calcularKg usa quantidade_kg salvo, fallback peso_por_metro, fallback tabela do banco
      const parede = m.detalhe?.includes('grossa') ? 'grossa' : 'fina';
      const kgTotal = m.unidade === 'm' ? calcularKg(m, qtd, parede) : null;
      const ehTuboCobre = kgTotal != null;

      return {
        tipo_item: m.item?.toLowerCase().includes('válvula') || m.item?.toLowerCase().includes('separador')
                     ? 'Componente' : 'Material',
        ref_id:    m.id || null,
        descricao: m.comprimento ? `${m.item} ${m.comprimento}m` : m.item,
        detalhe:   [m.detalhe || m.descricao, m.area_total ? `${fmtQtd(m.area_total)} m²` : detalheQtd].filter(Boolean).join(' — '),
        qtde:      ehTuboCobre ? kgTotal : qtd,
        unidade:   ehTuboCobre ? 'kg' : (m.unidade || 'un'),
        qtde_metros: ehTuboCobre ? qtd : null,
      };
    }),
    ...complementosPreenchidos.map(c => ({
      tipo_item: 'Complemento',
      ref_id:    null,
      descricao: c.descricao,
      detalhe:   '',
      qtde:      parseFloat(c.qtde) || 1,
      unidade:   c.unidade || 'un',
    })),
  ];

  const enviarWhatsApp = () => {
    const msg = encodeURIComponent(`Olá ${dadosCliente.contato || dadosCliente.nome || 'Cliente'}!\n\nOrçamento câmara frigorífica:\n*Total: R$ ${totalGeral.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}*\n\nEnvio o PDF em anexo.`);
    const tel = (dadosCliente.celular || '').replace(/\D/g, '');
    window.open(tel ? `https://api.whatsapp.com/send?phone=55${tel}&text=${msg}` : `https://api.whatsapp.com/send?text=${msg}`, '_blank');
  };

  return (
    <div className="space-y-6 pb-12 print:p-0 print:space-y-4">


      {/* ══ 1. LISTA COM CHECKBOXES ══ */}
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 shadow-sm print:hidden">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-amber-900 font-bold flex items-center gap-2">
            📋 Itens do Dimensionamento — Selecione o que incluir
          </h3>
          <button onClick={() => { if (window.confirm("Limpar todo o dimensionamento?")) aoReiniciar(); }}
            disabled={bloqueadoTrial}
            className="px-3 py-1.5 bg-amber-100 hover:bg-amber-200 text-amber-700 rounded-lg text-xs font-bold border border-amber-200 transition-all disabled:opacity-40 disabled:cursor-not-allowed">
            🗑️ LIMPAR TUDO
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Materiais */}
          <div>
            <h4 className="text-xs font-black text-amber-700 uppercase mb-3 tracking-widest">Materiais e Componentes</h4>
            {materiaisComEmbalagem.length === 0
              ? <p className="text-amber-600/50 italic text-sm">Nenhum material calculado.</p>
              : (materiaisComEmbalagem.map((item, i) => (
                <label key={i} className={`flex items-start gap-3 p-3 rounded-xl border mb-2 cursor-pointer transition-all ${materiaisAtivos[i] ? 'bg-white border-amber-200 shadow-sm' : 'bg-amber-50/30 border-amber-100 opacity-50'}`}>
                  <input type="checkbox" checked={!!materiaisAtivos[i]} onChange={() => toggleMaterial(i)} disabled={bloqueadoTrial} className="mt-0.5 w-4 h-4 accent-amber-600 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-bold leading-tight ${materiaisAtivos[i] ? 'text-slate-800' : 'text-slate-400 line-through'}`}>
                      {item.item}
                      {item.comprimento && (
                        <span className="font-normal text-slate-500 ml-1 text-xs">— {fmtQtd(item.comprimento)}m</span>
                      )}
                    </p>
                    <p className="text-[10px] text-slate-500 mt-0.5 truncate">{item.descricao || item.detalhe}</p>
                    {item.tipo_item === 'carga_fluido' && infoEmbalagem?.suficientes.length > 1 && (
                      <div className="flex items-center gap-1.5 mt-1.5 flex-wrap" onClick={e => e.preventDefault()}>
                        <span className="text-[9px] font-black text-amber-600 uppercase">Embalagem:</span>
                        {infoEmbalagem.suficientes.map(op => (
                          <button
                            key={op.peso_kg}
                            type="button"
                            onClick={() => setEmbalagemEscolhidaKg(op.peso_kg)}
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full border transition-all ${
                              embalagemEscolhidaKg === op.peso_kg
                                ? 'bg-amber-600 text-white border-amber-600'
                                : 'bg-white text-amber-700 border-amber-300 hover:bg-amber-100'}`}
                          >
                            {fmtQtd(op.peso_kg)}kg
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="text-right flex-shrink-0 ml-2">
                    <span className="text-amber-700 font-black text-xs block">
                      {qtdeExibir(item)}
                    </span>
                    {item.area_total && (
                      <span className="text-[10px] text-slate-400">({fmtQtd(item.area_total)} m²)</span>
                    )}
                  </div>
                </label>
              )))}
          </div>

          {/* Equipamentos */}
          <div>
            <h4 className="text-xs font-black text-amber-700 uppercase mb-3 tracking-widest">Equipamentos</h4>
            {(dadosAutomaticos?.equipamentos || []).length === 0
              ? <p className="text-amber-600/50 italic text-sm">Nenhum equipamento selecionado.</p>
              : (dadosAutomaticos.equipamentos.map((eq, i) => (
                <label key={i} className={`flex items-start gap-3 p-3 rounded-xl border mb-2 cursor-pointer transition-all ${equipamentosAtivos[i] ? 'bg-white border-emerald-200 shadow-sm' : 'bg-amber-50/30 border-amber-100 opacity-50'}`}>
                  <input type="checkbox" checked={!!equipamentosAtivos[i]} onChange={() => toggleEquipamento(i)} disabled={bloqueadoTrial} className="mt-0.5 w-4 h-4 accent-emerald-600 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-bold leading-tight ${equipamentosAtivos[i] ? 'text-emerald-800' : 'text-slate-400 line-through'}`}>
                      {eq.qtde > 1 ? `${eq.qtde}× ` : ''}{eq.nome}
                    </p>
                    <p className="text-[10px] text-slate-500 mt-0.5">{eq.detalhe}</p>
                  </div>
                  <button onClick={e => { e.preventDefault(); aoRemoverEquipamento(i); }}
                    className="w-6 h-6 flex-shrink-0 flex items-center justify-center rounded-full bg-red-50 text-red-400 hover:bg-red-500 hover:text-white transition-all text-xs" title="Remover">✕</button>
                </label>
              )))}
          </div>
        </div>

        {/* Complementos — adicionados junto com a seleção (editáveis aqui) */}
        <div className="mt-6 pt-5 border-t border-amber-200">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-bold text-amber-800 uppercase tracking-tight flex items-center gap-2">
              ➕ Complementos
              <span className="text-[10px] font-normal text-amber-600/70 normal-case">
                — fluido de limpeza, material elétrico, etc.
              </span>
            </h4>
            {onAbrirClassificacoes && (
              <button
                type="button"
                onClick={onAbrirClassificacoes}
                className="text-[10px] font-bold text-indigo-600 hover:underline whitespace-nowrap"
                title="Abrir gerenciador de classificações"
              >
                + Nova classificação
              </button>
            )}
          </div>

          <div className="space-y-2">
            {complementos.map((c, i) => (
              <div key={i} className="grid grid-cols-12 gap-2 items-center">
                <input
                  value={c.descricao} onChange={e => updateComplemento(i, 'descricao', e.target.value)}
                  placeholder="Descrição do item..."
                  className="col-span-4 px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-400 outline-none bg-white"
                />
                <select
                  value={c.classificacao_id ?? ''}
                  onChange={e => updateComplemento(i, 'classificacao_id', e.target.value ? parseInt(e.target.value) : null)}
                  className="col-span-3 px-2 py-2 rounded-lg border border-slate-300 text-xs bg-white outline-none focus:ring-2 focus:ring-indigo-400"
                  title="Classificação (define o bloco no orçamento)"
                >
                  <option value="">Outros / a classificar</option>
                  {classIndex.opcoes.map(o => <option key={o.id} value={o.id}>{o.label}</option>)}
                </select>
                <input
                  type="number" min="1" value={c.qtde} onChange={e => updateComplemento(i, 'qtde', e.target.value)}
                  className="col-span-1 px-2 py-2 rounded-lg border border-slate-300 text-sm text-center outline-none bg-white"
                />
                <input
                  value={c.unidade} onChange={e => updateComplemento(i, 'unidade', e.target.value)}
                  placeholder="un"
                  className="col-span-1 px-1 py-2 rounded-lg border border-slate-300 text-sm text-center outline-none bg-white"
                />
                <div className="col-span-2 relative">
                  <span className="absolute left-2 top-2 text-slate-400 text-xs">R$</span>
                  <input
                    type="number" min="0" step="0.01" value={c.preco_unit} onChange={e => updateComplemento(i, 'preco_unit', e.target.value)}
                    placeholder="0,00"
                    className="w-full pl-7 pr-1 py-2 rounded-lg border border-slate-300 text-sm outline-none bg-white"
                  />
                </div>
                <button onClick={() => complementos.length > 1 ? removerComplemento(i) : updateComplemento(i, 'descricao', '')}
                  className="col-span-1 text-slate-300 hover:text-red-400 transition-colors text-center">✕</button>
              </div>
            ))}
          </div>

          <p className="text-[10px] text-amber-600/70 mt-2 mb-3">
            💡 Deixe o valor em branco para itens "a cotação"
          </p>

          <button onClick={() => setComplementos([...complementos, novoComplemento()])}
            className="text-xs font-bold text-indigo-600 hover:underline flex items-center gap-1">
            + Adicionar complemento
          </button>
        </div>

        {/* Rodapé com botão APROVAR */}
        <div className={`mt-6 pt-5 border-t border-amber-200 flex flex-col sm:flex-row items-center justify-between gap-4 ${listaAprovada ? 'bg-emerald-50 -mx-6 -mb-6 px-6 pb-6 rounded-b-2xl' : ''}`}>
          <p className="text-sm text-amber-700 font-medium">
            <span className="font-black">{materiaisAprovados.length}</span> materiais +{' '}
            <span className="font-black">{equipamentosAprovados.length}</span> equipamentos
            {complementosPreenchidos.length > 0 && (
              <> + <span className="font-black">{complementosPreenchidos.length}</span> complementos</>
            )}{' '}selecionados
            {totalItens === 0 && <span className="text-red-500 ml-2">— selecione ao menos 1 item</span>}
          </p>
          {!listaAprovada ? (
            <button onClick={() => totalItens > 0 && setListaAprovada(true)} disabled={totalItens === 0}
              className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-sm shadow transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2">
              ✅ APROVAR LISTA E GERAR ORÇAMENTO
            </button>
          ) : (
            <div className="flex items-center gap-3">
              <span className="text-emerald-700 font-bold text-sm">✅ Lista aprovada — {totalItens} itens</span>
              <button onClick={() => setListaAprovada(false)} className="text-xs text-slate-500 hover:text-slate-700 underline">Revisar</button>
            </div>
          )}
        </div>
      </div>

      {/* ══ 2. CARRINHO (só após aprovar) ══ */}
      {listaAprovada && (
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden print:hidden animate-in fade-in duration-500">
          <div className="bg-slate-800 px-6 py-4 text-white flex justify-between items-center">
            <h3 className="font-bold flex items-center gap-2">📋 Lista de Engenharia</h3>
            <div className="flex items-center gap-3">
              <span className="text-[10px] bg-white/20 px-2 py-1 rounded uppercase font-bold tracking-widest">
                {totalItens} itens aprovados
              </span>
              <button
                onClick={() => { setListaAprovada(false); setOrcamento(null); }}
                className="text-[10px] font-bold text-slate-400 hover:text-white border border-slate-600 hover:border-slate-400 px-2 py-1 rounded transition-all"
                title="Voltar para a lista e alterar seleção"
              >
                ← Revisar lista
              </button>
            </div>
          </div>

          <div className="p-6 space-y-6">

            {/* Resumo dos itens aprovados (somente leitura) */}
            <div className="bg-slate-50 rounded-xl border border-slate-200 overflow-hidden">
              <div className="px-4 py-2 bg-slate-100 border-b border-slate-200 flex items-center justify-between">
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Itens do Dimensionamento</span>
                <div className="flex gap-2 items-center">
                  <button
                    onClick={() => exportarListaPDF()}
                    title={!projetoSalvo ? 'Salva o projeto e gera o PDF' : undefined}
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-lg transition-colors border flex items-center gap-1 ${
                      estaDesatualizada('listaPdf')
                        ? 'text-amber-700 bg-amber-50 hover:bg-amber-100 border-amber-300'
                        : 'text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 border-red-200'}`}
                  >
                    {estaDesatualizada('listaPdf') ? '🔄 Atualizar PDF' : '📄 PDF'}
                  </button>
                  <button
                    onClick={() => exportarListaExcel()}
                    title={!projetoSalvo ? 'Salva o projeto e gera o Excel' : undefined}
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-lg transition-colors border flex items-center gap-1 ${
                      estaDesatualizada('listaExcel')
                        ? 'text-amber-700 bg-amber-50 hover:bg-amber-100 border-amber-300'
                        : 'text-emerald-600 hover:text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border-emerald-200'}`}
                  >
                    {estaDesatualizada('listaExcel') ? '🔄 Atualizar Excel' : '📊 Excel'}
                  </button>
                </div>
              </div>
              <div className="divide-y divide-slate-100 max-h-48 overflow-y-auto">
                {equipamentosAprovados.map((e, i) => (
                  <div key={`eq-${i}`} className="flex items-center justify-between px-4 py-2">
                    <span className="text-sm text-emerald-700 font-semibold truncate">{e.qtde > 1 ? `${e.qtde}× ` : ''}{e.nome}</span>
                    <span className="text-[10px] text-slate-400 ml-2 flex-shrink-0">equipamento</span>
                  </div>
                ))}
                {materiaisAprovados.map((m, i) => (
                  <div key={`mat-${i}`} className="px-4 py-2 border-b border-slate-50 last:border-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <span className="text-sm text-slate-700 font-medium">
                          {m.item}
                          {m.comprimento && <span className="text-slate-400 ml-1 text-xs">— {fmtQtd(m.comprimento)}m</span>}
                        </span>
                        {/* Especificação do painel: nucleo, espessura, largura, fabricante */}
                        {(m.detalhe || m.descricao) && (
                          <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                            {m.detalhe || m.descricao}
                          </p>
                        )}
                        {m.aviso && (
                          <p className="text-[10px] text-red-600 mt-0.5 leading-tight font-semibold">
                            ⚠ {m.aviso}
                          </p>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400 flex-shrink-0 text-right">
                        <span className="block">{qtdeExibir(m)}</span>
                        {m.area_total && <span className="block">({fmtQtd(m.area_total)} m²)</span>}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Complementos — somente leitura (edite na lista de seleção acima) */}
            {complementosPreenchidos.length > 0 && (
              <div className="bg-slate-50 rounded-xl border border-slate-200 overflow-hidden">
                <div className="px-4 py-2 bg-slate-100 border-b border-slate-200">
                  <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Complementos e Materiais Adicionais</span>
                </div>
                <div className="divide-y divide-slate-100 max-h-40 overflow-y-auto">
                  {complementosPreenchidos.map((c, i) => (
                    <div key={i} className="flex items-center justify-between px-4 py-2">
                      <span className="text-sm text-slate-700 font-medium truncate">{c.descricao}</span>
                      <span className="text-[10px] text-slate-400 ml-2 flex-shrink-0 text-right whitespace-nowrap">
                        {fmtQtd(c.qtde)} {c.unidade}
                        {precoComplemento(c) > 0
                          ? ` · R$ ${(precoComplemento(c) * (parseFloat(c.qtde) || 1)).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                          : ' · a cotação'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── Bloco comercial (oculto no modo engenharia) ── */}
            {!modoEngenharia && (<>
            {/* Dados do Cliente */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <div className="flex items-center justify-between border-b pb-2 mb-4">
                <h4 className="text-sm font-bold text-slate-700 uppercase tracking-tight flex items-center gap-2">
                  👤 Dados do Cliente
                  {clienteSalvoId && <span className="text-[10px] bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-semibold">Cadastrado</span>}
                </h4>
                <div className="flex gap-2">
                  <button onClick={() => { setMostrarLista(p => !p); setModoNovoCliente(false); }}
                    className="text-xs px-3 py-1 rounded-lg bg-indigo-100 text-indigo-700 font-semibold hover:bg-indigo-200">
                    {mostrarLista ? 'Fechar' : '🔍 Buscar cliente'}
                  </button>
                  <button onClick={() => { setModoNovoCliente(true); setMostrarLista(false); setDadosCliente({ nome: '', cnpj: '', contato: '', celular: '', email: '' }); setClienteSalvoId(null); }}
                    className="text-xs px-3 py-1 rounded-lg bg-emerald-100 text-emerald-700 font-semibold hover:bg-emerald-200">
                    + Novo
                  </button>
                </div>
              </div>

              {/* Busca de cliente existente */}
              {mostrarLista && (
                <div className="mb-4">
                  <input value={buscaCliente} onChange={e => setBuscaCliente(e.target.value)}
                    placeholder="Buscar por nome, CNPJ ou e-mail..."
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none mb-2" autoFocus />
                  <div className="max-h-48 overflow-y-auto border border-slate-200 rounded-lg bg-white divide-y divide-slate-100">
                    {clientesFiltrados.length === 0
                      ? <p className="text-xs text-slate-400 p-3 text-center">Nenhum cliente encontrado</p>
                      : clientesFiltrados.map(c => (
                        <button key={c.id} onClick={() => selecionarCliente(c)}
                          className="w-full text-left px-4 py-2 hover:bg-indigo-50 transition-colors">
                          <p className="text-sm font-semibold text-slate-800">{c.nome}</p>
                          <p className="text-xs text-slate-500">{[c.cnpj, c.email].filter(Boolean).join(' · ')}</p>
                        </button>
                      ))
                    }
                  </div>
                </div>
              )}

              {/* Formulário de dados */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { name: 'nome',    label: 'Nome / Razão Social', ph: 'Frigorífico Silva LTDA', span: 1 },
                  { name: 'cnpj',    label: 'CNPJ / CPF',          ph: '00.000.000/0001-00',      span: 1 },
                  { name: 'contato', label: 'Pessoa de Contato',   ph: 'João Silva',              span: 1 },
                  { name: 'celular', label: 'Celular / WhatsApp',  ph: '(00) 00000-0000',         span: 1 },
                  { name: 'email',   label: 'E-mail',              ph: 'cliente@email.com',        span: 2 },
                ].map(f => (
                  <div key={f.name} className={`space-y-1 ${f.span === 2 ? 'md:col-span-2' : ''}`}>
                    <label className="text-[10px] font-bold text-slate-500 uppercase">{f.label}</label>
                    <input name={f.name} value={dadosCliente[f.name]} onChange={handleClienteChange}
                      placeholder={f.ph} type={f.name === 'email' ? 'email' : 'text'}
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none" />
                  </div>
                ))}
              </div>

              {/* Botão salvar cliente */}
              {dadosCliente.nome.trim() && (
                <div className="mt-3 flex justify-end">
                  <button onClick={salvarCliente}
                    className="text-xs px-4 py-1.5 rounded-lg bg-slate-700 text-white font-semibold hover:bg-slate-900">
                    {clienteSalvoId ? '💾 Atualizar cadastro' : '💾 Salvar cliente'}
                  </button>
                </div>
              )}
            </div>
            </>)}
          </div>

          {!modoEngenharia && (<>
          {/* Configurações da Proposta */}
          <div className="px-6 pb-4 border-t border-slate-100 pt-5 space-y-6">
            <h4 className="text-xs font-black text-slate-500 uppercase tracking-widest">⚙️ Composição da Proposta</h4>

            {/* Modo de faturamento */}
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase mb-2">Modo de faturamento</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {[
                  { v: 'empreitada', label: 'Empreitada', desc: 'Você fatura materiais + serviços ao cliente' },
                  { v: 'venda_direta', label: 'Faturamento direto', desc: 'Cliente compra do fornecedor; você cobra só a instalação' },
                ].map(opt => (
                  <label key={opt.v} className={`flex items-start gap-2 p-3 rounded-xl border cursor-pointer text-xs transition-all ${modoFaturamento === opt.v ? 'bg-indigo-50 border-indigo-300' : 'bg-slate-50 border-slate-200'}`}>
                    <input type="radio" checked={modoFaturamento === opt.v} onChange={() => setModoFaturamento(opt.v)} className="accent-indigo-600 mt-0.5" />
                    <span><b>{opt.label}</b><br /><span className="text-slate-500">{opt.desc}</span></span>
                  </label>
                ))}
              </div>
            </div>

            {/* Exibição de materiais — só no faturamento direto */}
            {modoFaturamento === 'venda_direta' && (
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase mb-2">Como apresentar os materiais na proposta</p>
                <div className="space-y-2">
                  {[
                    { v: 'itemizado', label: 'Lista completa', desc: 'Itens com qtde e valores de cotação (sem margem) + lembrete de faturamento direto' },
                    { v: 'resumo',    label: 'Resumo global',  desc: 'Uma linha "Cj. materiais" com o valor total de cotação + serviços' },
                    { v: 'sem_preco', label: 'Descritivo sem preço', desc: 'Itens e quantidades sem nenhum valor; investimento mostra só os serviços' },
                  ].map(opt => (
                    <label key={opt.v} className={`flex items-start gap-2 p-3 rounded-xl border cursor-pointer text-xs transition-all ${exibicaoMateriais === opt.v ? 'bg-amber-50 border-amber-300' : 'bg-slate-50 border-slate-200'}`}>
                      <input type="radio" checked={exibicaoMateriais === opt.v} onChange={() => setExibicaoMateriais(opt.v)} className="accent-amber-600 mt-0.5" />
                      <span><b>{opt.label}</b><br /><span className="text-slate-500">{opt.desc}</span></span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Lista de materiais na empreitada */}
            {modoFaturamento === 'empreitada' && (
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase mb-2">Como apresentar os materiais na proposta</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {[
                    { v: 'completa', label: 'Lista completa', desc: 'Exibe todos os itens com preço de venda (markup aplicado)' },
                    { v: 'totais',   label: 'Somente totais', desc: 'Omite a lista de itens; mostra apenas os valores de investimento' },
                  ].map(opt => (
                    <label key={opt.v} className={`flex items-start gap-2 p-3 rounded-xl border cursor-pointer text-xs transition-all ${listaEmpreitada === opt.v ? 'bg-indigo-50 border-indigo-300' : 'bg-slate-50 border-slate-200'}`}>
                      <input type="radio" checked={listaEmpreitada === opt.v} onChange={() => setListaEmpreitada(opt.v)} className="accent-indigo-600 mt-0.5" />
                      <span><b>{opt.label}</b><br /><span className="text-slate-500">{opt.desc}</span></span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Mão de obra e custos */}
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase mb-2">Composição de custos de serviços</p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {[
                  { k: 'mo_paineis',       label: 'MO Painéis (R$)' },
                  { k: 'mo_refrigeracao',  label: 'MO Refrigeração (R$)' },
                  { k: 'locomocao',        label: 'Locomoção (R$)' },
                  { k: 'despesas',         label: 'Despesas (R$)' },
                  { k: 'outros',           label: 'Outros (R$)' },
                ].map(f => (
                  <div key={f.k} className="space-y-1">
                    <label className="text-[9px] font-bold text-slate-500 uppercase">{f.label}</label>
                    <div className="relative">
                      <span className="absolute left-2 top-1.5 text-slate-400 text-xs">R$</span>
                      <input type="number" min="0" step="0.01" value={custos[f.k]}
                        onChange={e => setCustos(p => ({ ...p, [f.k]: e.target.value }))}
                        placeholder="0,00"
                        className="w-full pl-8 pr-2 py-1.5 rounded-lg border border-slate-300 text-xs outline-none focus:ring-2 focus:ring-indigo-400" />
                    </div>
                  </div>
                ))}
              </div>
              <label className="flex items-center gap-2 mt-2 cursor-pointer text-xs text-slate-600">
                <input type="checkbox" checked={moSeparada} onChange={e => setMoSeparada(e.target.checked)} className="accent-indigo-600" />
                Apresentar MO painéis e MO refrigeração separadas na proposta
              </label>
            </div>

            {/* Margem, impostos, apresentação */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-500 uppercase">Margem Materiais (%)</label>
                <input type="number" min="0" max="98" step="0.5" value={margemMateriais}
                  onChange={e => setMargemMateriais(e.target.value)}
                  disabled={modoFaturamento === 'venda_direta'}
                  title={modoFaturamento === 'venda_direta' ? 'No faturamento direto os materiais vão a custo de cotação, sem margem' : ''}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs outline-none focus:ring-2 focus:ring-indigo-400 disabled:bg-slate-100 disabled:text-slate-400" />
              </div>
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-500 uppercase">Margem Serviços (%)</label>
                <input type="number" min="0" max="98" step="0.5" value={margemServicos}
                  onChange={e => setMargemServicos(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs outline-none focus:ring-2 focus:ring-indigo-400" />
              </div>
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-500 uppercase">Impostos (%)</label>
                <input type="number" min="0" max="50" step="0.5" value={imposto}
                  onChange={e => setImposto(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs outline-none focus:ring-2 focus:ring-indigo-400" />
              </div>
              <div className="space-y-1 col-span-2">
                <label className="text-[9px] font-bold text-slate-500 uppercase">
                  {modoFaturamento === 'venda_direta' ? 'Apresentação da mão de obra' : 'Apresentação dos valores'}
                </label>
                {modoFaturamento === 'venda_direta' && exibicaoMateriais === 'resumo' ? (
                  <p className="text-[10px] text-slate-400 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
                    No resumo global a apresentação é fixa: conjunto de materiais + serviços + total.
                  </p>
                ) : (
                  <div className="flex gap-2">
                    {[{ v: 'blocos', l: 'Por blocos' }, { v: 'global', l: 'Valor global' }].map(o => (
                      <label key={o.v} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border cursor-pointer text-xs flex-1 justify-center transition-all ${apresentacao === o.v ? 'bg-indigo-50 border-indigo-300 font-bold text-indigo-700' : 'bg-slate-50 border-slate-200 text-slate-600'}`}>
                        <input type="radio" checked={apresentacao === o.v} onChange={() => setApresentacao(o.v)} className="accent-indigo-600" />
                        {o.l}
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Objeto da proposta */}
            <div className="space-y-1">
              <label className="text-[9px] font-bold text-slate-500 uppercase">Objeto da proposta</label>
              <textarea rows={2} value={resumoObjeto} onChange={e => setResumoObjeto(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs outline-none focus:ring-2 focus:ring-indigo-400 resize-none" />
            </div>

            {/* Condições comerciais */}
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase mb-2">Condições comerciais</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[
                  { k: 'pagamento',       label: 'Condições de pagamento', rows: 2 },
                  { k: 'prazo_execucao',  label: 'Prazo de execução',      rows: 1 },
                  { k: 'garantia',        label: 'Garantia',               rows: 2 },
                  { k: 'incluso',         label: 'Está incluso',           rows: 3 },
                  { k: 'nao_incluso',     label: 'Não está incluso',       rows: 3 },
                ].map(f => (
                  <div key={f.k} className={`space-y-1 ${f.rows >= 3 ? 'sm:col-span-1' : ''}`}>
                    <label className="text-[9px] font-bold text-slate-500 uppercase">{f.label}</label>
                    <textarea rows={f.rows} value={cond[f.k]} onChange={e => setCond(p => ({ ...p, [f.k]: e.target.value }))}
                      className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs outline-none focus:ring-2 focus:ring-indigo-400 resize-none" />
                  </div>
                ))}
                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-slate-500 uppercase">Validade da proposta (dias)</label>
                  <input type="number" min="1" value={cond.validade_dias} onChange={e => setCond(p => ({ ...p, validade_dias: e.target.value }))}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs outline-none focus:ring-2 focus:ring-indigo-400" />
                </div>
              </div>
            </div>

            {/* Conteúdo da proposta */}
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase mb-2">Conteúdo da proposta</p>
              <div className="flex flex-wrap gap-4">
                {resumoTecnico && (
                  <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-700">
                    <input type="checkbox" checked={incluirResumoTecnico} onChange={e => setIncluirResumoTecnico(e.target.checked)} className="accent-indigo-600" />
                    Incluir resumo técnico
                  </label>
                )}
              </div>
            </div>
          </div>

          <div className="p-6 bg-slate-50 border-t border-slate-100">
            {/* Duas opções para o técnico */}
            <p className="text-center text-xs text-slate-400 mb-4 font-medium uppercase tracking-widest">
              O que deseja fazer com esta lista?
            </p>

            {/* Trava: cotação e orçamento exigem projeto salvo (vínculo no histórico) */}
            {!projetoSalvo && (
              <div className="mb-4 p-3 bg-amber-50 border border-amber-300 rounded-xl text-center">
                <p className="text-sm font-bold text-amber-800">
                  💾 Salve o projeto antes de cotar ou orçar
                </p>
                <p className="text-[11px] text-amber-600 mt-1">
                  Use o botão <b>Salvar</b> no topo da tela. A cotação e a proposta ficam vinculadas ao projeto — sem isso o histórico se perde.
                </p>
              </div>
            )}

            {estaDesatualizada('cotacao') && (
              <div className="mb-3 p-2.5 bg-amber-50 border border-amber-300 rounded-lg text-center text-[11px] text-amber-800 font-semibold">
                ⚠️ Os itens mudaram desde a última cotação gerada. Gere uma nova planilha para incluir as alterações.
              </div>
            )}

            {baseDesatualizada && (
              <div className="mb-3 p-3 bg-orange-50 border border-orange-300 rounded-lg flex flex-col sm:flex-row items-center justify-between gap-2">
                <span className="text-[11px] text-orange-800 font-semibold">
                  🔁 A base de preços foi atualizada (o fornecedor reenviou a cotação). Os preços deste orçamento podem estar desatualizados.
                </span>
                <button onClick={verificarEGerar} disabled={loading || loadingCotacaoCheck}
                  className="text-[11px] font-bold px-3 py-1.5 rounded-lg bg-orange-600 text-white hover:bg-orange-700 disabled:opacity-50 whitespace-nowrap">
                  🔄 Atualizar base de preços
                </button>
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">

              {/* Opção A: Enviar para cotação */}
              <button onClick={() => setModalCotacaoAberto(true)} disabled={loading || !projetoSalvo || bloqueadoTrial}
                title={!projetoSalvo ? 'Salve o projeto primeiro' : ''}
                className={`w-full sm:w-auto px-6 py-3 text-white rounded-xl font-bold text-sm shadow transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 ${
                  estaDesatualizada('cotacao') ? 'bg-amber-600 hover:bg-amber-700 ring-2 ring-amber-300' : 'bg-amber-500 hover:bg-amber-600'}`}>
                📊 GERAR PLANILHA DE COTAÇÃO
                <span className="text-[10px] font-normal opacity-80">— enviar ao fornecedor</span>
              </button>

              <span className="text-slate-300 font-bold hidden sm:block">ou</span>

              {/* Opção B: Gera proposta (verifica cotação primeiro) */}
              <button onClick={verificarEGerar} disabled={loading || loadingCotacaoCheck || !projetoSalvo || bloqueadoTrial}
                title={!projetoSalvo ? 'Salve o projeto primeiro' : ''}
                className="w-full sm:w-auto px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-sm shadow-lg hover:-translate-y-0.5 transition-all disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                💰 GERAR PROPOSTA AO CLIENTE
                <span className="text-[10px] font-normal opacity-80">— usar preços da cotação</span>
              </button>
            </div>
            {(loading || loadingCotacaoCheck) && <p className="text-center text-xs text-slate-400 mt-3 animate-pulse">Processando...</p>}

            {/* Aviso: nenhuma cotação */}
            {cotacaoAviso === 'nenhuma' && (
              <div className="mt-4 p-4 bg-amber-50 border border-amber-300 rounded-xl">
                <p className="font-bold text-amber-800 text-sm">📋 Nenhuma cotação encontrada para este projeto</p>
                <p className="text-xs text-amber-700 mt-1">
                  Para gerar uma proposta com preços reais, você precisa primeiro gerar a planilha de cotação,
                  enviá-la ao fornecedor e importar a planilha devolvida com os preços.
                </p>
                <div className="flex flex-wrap gap-2 mt-3">
                  <button onClick={() => { setCotacaoAviso(null); setModalCotacaoAberto(true); }}
                    className="text-xs px-3 py-1.5 rounded-lg bg-amber-500 text-white font-bold hover:bg-amber-600">
                    📊 Gerar planilha de cotação
                  </button>
                  {onAbrirPainelCotacoes && (
                    <button onClick={() => { setCotacaoAviso(null); onAbrirPainelCotacoes(); }}
                      className="text-xs px-3 py-1.5 rounded-lg bg-amber-100 text-amber-800 font-bold hover:bg-amber-200 border border-amber-300">
                      Ver painel de cotações
                    </button>
                  )}
                  <button onClick={() => { setCotacaoAviso(null); gerarOrcamentoComPrecos(); }}
                    className="text-xs px-3 py-1.5 rounded-lg bg-white text-amber-700 font-bold hover:bg-amber-50 border border-amber-300"
                    title="Usa a lista de preços cadastrada da sua empresa (Catálogo de Preços, no menu) — sem precisar cotar com fornecedor">
                    💰 Gerar com meu catálogo de preços
                  </button>
                </div>
              </div>
            )}

            {/* Aviso: cotação em andamento, sem processada */}
            {cotacaoAviso === 'aguardando' && (
              <div className="mt-4 p-4 bg-blue-50 border border-blue-300 rounded-xl">
                <p className="font-bold text-blue-800 text-sm">⏳ Aguardando retorno do fornecedor</p>
                <p className="text-xs text-blue-700 mt-1">
                  {cotacoesEmAndamento.length === 1
                    ? `Cotação ${cotacoesEmAndamento[0].codigo} foi enviada mas os preços ainda não foram importados.`
                    : `${cotacoesEmAndamento.length} cotações enviadas, mas nenhuma teve os preços confirmados ainda.`}
                  {' '}Quando o fornecedor devolver a planilha, importe-a no painel de cotações.
                </p>
                {onAbrirPainelCotacoes && (
                  <button onClick={() => { setCotacaoAviso(null); onAbrirPainelCotacoes(); }}
                    className="mt-3 text-xs px-3 py-1.5 rounded-lg bg-blue-600 text-white font-bold hover:bg-blue-700">
                    Abrir painel de cotações
                  </button>
                )}
              </div>
            )}
          </div>
          </>)}

          {modoEngenharia && (
            <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg text-center text-[11px] text-indigo-800 font-semibold">
              📋 Modo engenharia — exporte a lista de itens acima (Excel/PDF). A jornada de orçamento está desativada nas Configurações.
            </div>
          )}
        </div>
      )}

      {/* Modal de escolha de cotação (múltiplas processadas) */}
      {modalEscolhaCotacao && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6">
            <h3 className="text-base font-black text-slate-900 mb-1">Escolha a cotação para a proposta</h3>
            <p className="text-xs text-slate-500 mb-4">Há {cotacoesProcessadas.length} cotações com preços confirmados para este projeto.</p>

            <div className="space-y-2 mb-4">
              {/* Opção melhor preço */}
              <label className="flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-colors"
                style={{ borderColor: cotacaoEscolhidaId === null ? '#4f46e5' : '#e2e8f0', background: cotacaoEscolhidaId === null ? '#eef2ff' : '' }}>
                <input type="radio" name="cotacao" checked={cotacaoEscolhidaId === null}
                  onChange={() => setCotacaoEscolhidaId(null)} className="mt-0.5" />
                <div>
                  <p className="text-sm font-bold text-indigo-700">⭐ Usar melhor preço por item</p>
                  <p className="text-[11px] text-slate-500">Compara todas as cotações e seleciona o menor preço para cada item individualmente.</p>
                </div>
              </label>

              {/* Uma por uma */}
              {cotacoesProcessadas.map(c => (
                <label key={c.id} className="flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-colors"
                  style={{ borderColor: cotacaoEscolhidaId === c.id ? '#4f46e5' : '#e2e8f0', background: cotacaoEscolhidaId === c.id ? '#eef2ff' : '' }}>
                  <input type="radio" name="cotacao" checked={cotacaoEscolhidaId === c.id}
                    onChange={() => setCotacaoEscolhidaId(c.id)} className="mt-0.5" />
                  <div>
                    <p className="text-sm font-bold text-slate-800">{c.codigo}</p>
                    <p className="text-[11px] text-slate-500">Processada em {c.data_recebimento ? new Date(c.data_recebimento).toLocaleDateString('pt-BR') : '—'}</p>
                  </div>
                </label>
              ))}
            </div>

            <div className="flex justify-end gap-3">
              <button onClick={() => setModalEscolhaCotacao(false)}
                className="text-xs px-4 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50">
                Cancelar
              </button>
              <button onClick={confirmarEscolhaCotacao} disabled={loading || bloqueadoTrial}
                className="text-xs px-4 py-2 rounded-lg bg-indigo-600 text-white font-bold hover:bg-indigo-700 disabled:opacity-50">
                {loading ? 'Gerando...' : 'Gerar proposta'}
              </button>
            </div>
          </div>
        </div>
      )}

      {erro && <div className="p-4 bg-red-100 text-red-700 rounded-xl text-center font-bold border border-red-200">{erro}</div>}

      {/* Itens sem preço na cotação — permite entrada manual */}
      {orcamento && itensSemPreco.length > 0 && (
        <div className="p-4 bg-amber-50 border border-amber-300 rounded-2xl print:hidden">
          <p className="font-bold text-amber-800 text-sm mb-1">
            ⚠️ {itensSemPreco.length} {itensSemPreco.length === 1 ? 'item sem preço' : 'itens sem preço'} na cotação
          </p>
          <p className="text-xs text-amber-700 mb-3">
            Os itens abaixo não foram encontrados na cotação ou estão sem valor. Você pode informar o preço manualmente e recalcular.
          </p>
          <div className="space-y-2">
            {itensSemPreco.map(desc => (
              <div key={desc} className="flex items-center gap-3">
                <span className="text-xs text-slate-700 flex-1 truncate" title={desc}>{desc}</span>
                <div className="relative w-32 flex-shrink-0">
                  <span className="absolute left-2 top-1.5 text-slate-400 text-xs">R$</span>
                  <input type="number" min="0" step="0.01"
                    value={precosManuals[norm(desc)] ?? ''}
                    onChange={e => setPrecosManuals(p => ({ ...p, [norm(desc)]: e.target.value }))}
                    disabled={bloqueadoTrial}
                    placeholder="0,00"
                    className="w-full pl-7 pr-2 py-1.5 rounded-lg border border-amber-300 text-xs outline-none focus:ring-2 focus:ring-amber-400 bg-white disabled:opacity-50" />
                </div>
              </div>
            ))}
          </div>
          <button onClick={recalcularComPrecosManuals} disabled={loading || bloqueadoTrial}
            className="mt-3 text-xs px-4 py-2 rounded-lg bg-amber-600 text-white font-bold hover:bg-amber-700 disabled:opacity-50">
            {loading ? 'Recalculando...' : '🔄 Recalcular proposta com esses preços'}
          </button>
        </div>
      )}

      {/* Modal de cotação com fornecedor */}
      <ModalCotacaoFornecedor
        aberto={modalCotacaoAberto}
        aoFechar={() => setModalCotacaoAberto(false)}
        itens={modalCotacaoAberto ? montarItensCotacao() : []}
        nomeProjeto={projetoAtual?.nome || (dadosCliente.nome ? `Câmara Frigorífica — ${dadosCliente.nome}` : 'Câmara Frigorífica')}
        projetoId={projetoAtual?.id || null}
        aoGerar={() => marcarGerada('cotacao')}
      />

      {/* ══ 3. RESUMO FINANCEIRO PRIVADO (não imprime) ══ */}
      {orcamento && !modoEngenharia && (
        <div className="bg-slate-800 text-white rounded-2xl p-6 print:hidden space-y-5">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest">🔒 Resumo Financeiro Interno</h4>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-700 text-slate-400 font-bold uppercase">
              {modoFaturamento === 'venda_direta'
                ? `Faturamento direto · Margem serviços ${fmtQtd(margemServicos)}% · Imposto ${fmtQtd(imposto)}%`
                : `Empreitada · Margem mat. ${fmtQtd(margemMateriais)}% · serv. ${fmtQtd(margemServicos)}% · Imposto ${fmtQtd(imposto)}%`}
            </span>
          </div>

          {/* Base de preços (rastreabilidade — uso interno) */}
          {baseCotacao?.cotacoes?.length > 0 && (
            <div className={`rounded-xl px-4 py-2.5 text-[11px] flex items-center gap-2 ${
              baseDesatualizada ? 'bg-orange-900/40 text-orange-200' : 'bg-slate-700/40 text-slate-300'}`}>
              <span>📎</span>
              <span>Base de preços: <span className="font-semibold text-white">{textoBaseCotacao()}</span></span>
              {baseDesatualizada && <span className="ml-auto font-bold text-orange-300">⚠️ atualizada — regere</span>}
            </div>
          )}

          {/* Composição de custos de serviços */}
          {cf.custo_servicos > 0 && (
            <div className="bg-slate-700/40 rounded-xl p-4">
              <p className="text-[9px] font-bold text-slate-400 uppercase mb-3">Composição dos custos de serviços</p>
              <div className="space-y-1.5">
                {[
                  { label: 'MO montagem de painéis',          value: parseFloat(custos.mo_paineis)      || 0 },
                  { label: 'MO montagem de refrigeração',     value: parseFloat(custos.mo_refrigeracao) || 0 },
                  { label: 'Locomoção',                       value: parseFloat(custos.locomocao)       || 0 },
                  { label: 'Despesas',                        value: parseFloat(custos.despesas)        || 0 },
                  { label: 'Outros',                          value: parseFloat(custos.outros)          || 0 },
                ].filter(r => r.value > 0).map(r => (
                  <div key={r.label} className="flex justify-between text-xs">
                    <span className="text-slate-400">{r.label}</span>
                    <span className="text-slate-200 font-bold tabular-nums">R$ {fmt(r.value)}</span>
                  </div>
                ))}
                <div className="flex justify-between text-xs border-t border-slate-600 pt-1.5 mt-1.5">
                  <span className="text-slate-300 font-bold">Total custo serviços</span>
                  <span className="text-yellow-300 font-black tabular-nums">R$ {fmt(cf.custo_servicos)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">× fator markup (1 / (1 − {fmtQtd(margemServicos)}% − {fmtQtd(imposto)}%))</span>
                  <span className="text-green-300 font-black tabular-nums">R$ {fmt(cf.preco_servicos_cliente)}</span>
                </div>
              </div>
            </div>
          )}

          {/* Fluxo financeiro */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {modoFaturamento === 'venda_direta' ? (
              <>
                <div className="bg-slate-700/50 rounded-xl p-3">
                  <p className="text-[9px] font-bold text-slate-400 uppercase">Materiais (repasse)</p>
                  <p className="text-sm font-black text-slate-300">R$ {fmt(cf.custo_materiais)}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">Faturado pelo fornecedor</p>
                </div>
                <div className="bg-slate-700/50 rounded-xl p-3">
                  <p className="text-[9px] font-bold text-slate-400 uppercase">Serviços (seu faturamento)</p>
                  <p className="text-sm font-black text-green-300">R$ {fmt(cf.preco_servicos_cliente)}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">Custo R$ {fmt(cf.custo_servicos)}</p>
                </div>
                <div className="bg-slate-700/50 rounded-xl p-3">
                  <p className="text-[9px] font-bold text-slate-400 uppercase">Impostos s/ serviços</p>
                  <p className="text-sm font-black text-red-300">R$ {fmt(cf.impostos_valor)}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">{fmtQtd(imposto)}% sobre serviços</p>
                </div>
                <div className="bg-slate-700/50 rounded-xl p-3">
                  <p className="text-[9px] font-bold text-slate-400 uppercase">Lucro líquido</p>
                  <p className={`text-sm font-black ${cf.lucro_liquido >= 0 ? 'text-emerald-300' : 'text-red-400'}`}>R$ {fmt(cf.lucro_liquido)}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">Serviços − custo − impostos</p>
                </div>
              </>
            ) : (
              <>
                <div className="bg-slate-700/50 rounded-xl p-3">
                  <p className="text-[9px] font-bold text-slate-400 uppercase">Custo total</p>
                  <p className="text-sm font-black text-yellow-300">R$ {fmt(cf.custo_total)}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">Mat. R$ {fmt(cf.custo_materiais)} + Serv. R$ {fmt(cf.custo_servicos)}</p>
                </div>
                <div className="bg-slate-700/50 rounded-xl p-3">
                  <p className="text-[9px] font-bold text-slate-400 uppercase">Preço de venda</p>
                  <p className="text-sm font-black text-green-300">R$ {fmt(cf.preco_venda)}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">Custo × fator markup</p>
                </div>
                <div className="bg-slate-700/50 rounded-xl p-3">
                  <p className="text-[9px] font-bold text-slate-400 uppercase">Impostos estimados</p>
                  <p className="text-sm font-black text-red-300">R$ {fmt(cf.impostos_valor)}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">{fmtQtd(imposto)}% sobre faturamento</p>
                </div>
                <div className="bg-slate-700/50 rounded-xl p-3">
                  <p className="text-[9px] font-bold text-slate-400 uppercase">Lucro líquido</p>
                  <p className={`text-sm font-black ${cf.lucro_liquido >= 0 ? 'text-emerald-300' : 'text-red-400'}`}>R$ {fmt(cf.lucro_liquido)}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">Venda − custo − impostos</p>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* ══ 4. PROPOSTA FINAL ══ */}
      {orcamento && !modoEngenharia && (
        <div ref={propostaRef} className="bg-white border-2 border-slate-900 rounded-2xl overflow-hidden shadow-2xl animate-in fade-in slide-in-from-bottom-8 duration-700 print:shadow-none print:border-none print:rounded-none print:m-0 print:p-0">

          {/* Cabeçalho */}
          <div className="bg-slate-900 text-white px-8 py-6 print:bg-white print:text-slate-900 print:border-b-2 print:border-slate-900 print:px-0">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.3em] print:text-slate-500">Proposta Técnica Comercial</p>
                <h3 className="text-3xl font-black tracking-tighter mt-1 leading-none">{dadosCliente.nome || 'Cliente não informado'}</h3>
                <p className="text-slate-300 text-sm mt-1 print:text-slate-600">{resumoObjeto}</p>
              </div>
              <div className="text-right flex-shrink-0 ml-6 space-y-1">
                <div>
                  <p className="text-[9px] text-slate-400 uppercase font-bold">Emissão</p>
                  <p className="text-sm font-bold">{new Date().toLocaleDateString('pt-BR')}</p>
                </div>
                <div>
                  <p className="text-[9px] text-slate-400 uppercase font-bold">Validade</p>
                  <p className="text-sm font-bold">
                    {new Date(Date.now() + (parseInt(cond.validade_dias) || 10) * 86400000).toLocaleDateString('pt-BR')}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="p-8 space-y-10 print:px-0 print:py-6">

            {/* Dados do cliente */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-50 p-6 rounded-xl border border-slate-200 relative print:bg-white print:border-slate-300">
              <button onClick={() => setOrcamento(null)}
                className="absolute top-4 right-4 bg-white border border-slate-200 p-2 rounded-lg text-xs font-bold text-slate-400 hover:text-indigo-600 hover:border-indigo-200 transition-all shadow-sm print:hidden flex items-center gap-1">
                ✏️ EDITAR
              </button>
              <div className="space-y-1">
                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Informações do Cliente</h4>
                <p className="text-lg font-black text-slate-900">{dadosCliente.nome || '---'}</p>
                {dadosCliente.cnpj && <p className="text-sm text-slate-600">CNPJ/CPF: <b>{dadosCliente.cnpj}</b></p>}
              </div>
              <div className="grid grid-cols-2 gap-3 pt-4 md:pt-0 border-t md:border-t-0 md:border-l border-slate-200 md:pl-6">
                {[['Contato', dadosCliente.contato], ['Celular', dadosCliente.celular]].map(([l, v]) => (
                  <div key={l}><p className="text-[9px] font-black text-slate-400 uppercase">{l}</p><p className="text-sm font-bold text-slate-800">{v || '---'}</p></div>
                ))}
                <div className="col-span-2"><p className="text-[9px] font-black text-slate-400 uppercase">E-mail</p><p className="text-sm font-bold text-slate-800">{dadosCliente.email || '---'}</p></div>
              </div>
            </div>

            {/* Resumo Técnico */}
            {incluirResumoTecnico && resumoTecnico && (
              <div className="bg-slate-50 rounded-xl border border-slate-200 p-5">
                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">Especificações Técnicas</h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                  {[
                    { l: 'Comprimento', v: resumoTecnico.comprimento, u: 'm' },
                    { l: 'Largura',     v: resumoTecnico.largura,     u: 'm' },
                    { l: 'Altura',      v: resumoTecnico.altura,      u: 'm' },
                    { l: 'T. Interna',  v: resumoTecnico.temperatura_interna, u: '°C' },
                  ].map(x => (
                    <div key={x.l} className="bg-white rounded-lg p-3 border border-slate-100">
                      <p className="text-[9px] font-black text-slate-400 uppercase">{x.l}</p>
                      <p className="text-lg font-black text-slate-900">{x.v}<span className="text-xs font-normal text-slate-400"> {x.u}</span></p>
                    </div>
                  ))}
                </div>
                <div className="mt-3 bg-white rounded-lg p-3 border border-slate-100 flex items-center justify-between">
                  <p className="text-xs text-slate-500">Isolamento</p>
                  <p className="text-sm font-bold text-slate-800">{resumoTecnico.nucleo} {resumoTecnico.espessura}mm</p>
                </div>
                {resumoTecnico.carga_termica && (
                  <div className="mt-3 bg-emerald-50 rounded-xl p-4 border border-emerald-200">
                    <div className="flex items-center justify-between flex-wrap gap-3">
                      <div>
                        <p className="text-[10px] font-black text-emerald-600 uppercase tracking-widest">Carga Térmica Calculada</p>
                        <p className="text-2xl font-black text-emerald-800">{Number(resumoTecnico.carga_termica).toLocaleString('pt-BR')} <span className="text-base font-normal">kcal/h</span></p>
                      </div>
                      <div className="flex gap-5 text-right">
                        {resumoTecnico.produto && (
                          <div><p className="text-[9px] font-black text-slate-400 uppercase">Produto</p><p className="text-sm font-bold text-slate-800">{resumoTecnico.produto}</p></div>
                        )}
                        {resumoTecnico.movimentacao != null && resumoTecnico.movimentacao !== '' && Number(resumoTecnico.movimentacao) > 0 && (
                          <div><p className="text-[9px] font-black text-slate-400 uppercase">Movimentação</p><p className="text-sm font-bold text-slate-800">{fmtQtd(resumoTecnico.movimentacao)} kg/dia</p></div>
                        )}
                        {resumoTecnico.temp_entrada != null && resumoTecnico.temp_entrada !== '' && (
                          <div><p className="text-[9px] font-black text-slate-400 uppercase">Temp. Entrada</p><p className="text-sm font-bold text-slate-800">{fmtQtd(resumoTecnico.temp_entrada)} °C</p></div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Planta técnica */}
            {dadosAutomaticos?.imagem_projeto && (
              <div className="border border-slate-200 rounded-xl overflow-hidden bg-slate-50 p-4">
                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">Planta Técnica da Câmara Frigorífica</h4>
                <img src={dadosAutomaticos.imagem_projeto} alt="Planta" className="max-h-[300px] mx-auto object-contain print:max-h-[400px]" />
              </div>
            )}

            {/* Escopo */}
            {(cond.incluso || cond.nao_incluso) && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {cond.incluso && (
                  <div className="bg-green-50 border border-green-200 rounded-xl p-5">
                    <h4 className="text-[10px] font-black text-green-700 uppercase tracking-[0.2em] mb-2">✅ Está incluído</h4>
                    <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">{cond.incluso}</p>
                  </div>
                )}
                {cond.nao_incluso && (
                  <div className="bg-red-50 border border-red-200 rounded-xl p-5">
                    <h4 className="text-[10px] font-black text-red-700 uppercase tracking-[0.2em] mb-2">❌ Não está incluído</h4>
                    <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">{cond.nao_incluso}</p>
                  </div>
                )}
              </div>
            )}

            {/* Lista detalhada de itens (omitida no resumo global do fat. direto e no "somente totais" da empreitada) */}
            {!(modoFaturamento === 'venda_direta' && exibicaoMateriais === 'resumo')
              && !(modoFaturamento === 'empreitada' && listaEmpreitada === 'totais') && (
              <>
                {modoFaturamento === 'venda_direta' && exibicaoMateriais === 'itemizado' && (
                  <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-xs text-amber-800">
                    <b>Faturamento direto:</b> os materiais e equipamentos abaixo serão faturados
                    diretamente pelo fornecedor ao cliente, pelos valores de cotação, sem margem.
                  </div>
                )}
                {Object.entries(agruparPorBloco(orcamento.detalhamento_itens)).map(([cat, itens]) =>
                  itens.length > 0 && (
                    <div key={cat}>
                      <h4 className={`flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] mb-4 border-b border-slate-100 pb-2 ${corDoBloco(cat).texto}`}>
                        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${corDoBloco(cat).dot}`} />
                        {cat}
                      </h4>
                      <div className="space-y-3">
                        {itens.map((l, i) => (
                          <div key={i} className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="font-bold text-slate-800 text-sm leading-tight">{l.item}</div>
                              {l.detalhe && <div className="text-xs text-slate-400 mt-0.5">{l.detalhe}</div>}
                            </div>
                            <div className="w-24 text-center text-sm text-slate-600 font-medium">{fmtQtd(l.quantidade)} {l.unidade}</div>
                            <div className="w-32 text-right font-black text-slate-900 text-sm">
                              {modoFaturamento === 'venda_direta'
                                ? (exibicaoMateriais === 'sem_preco' ? null : `R$ ${fmt(l.custo_total_rs ?? 0)}`)
                                : `R$ ${fmt((l.custo_total_rs ?? 0) * cf.fatorMateriais)}`}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                )}
                {complementosPreenchidos.length > 0 && (
                  <div>
                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4 border-b border-slate-100 pb-2">Complementos e Materiais Adicionais</h4>
                    <div className="space-y-3">
                      {complementosPreenchidos.map((c, i) => (
                        <div key={i} className="flex justify-between items-start">
                          <div className="flex-1 font-bold text-slate-800 text-sm">{c.descricao}</div>
                          <div className="w-24 text-center text-sm text-slate-600 font-medium">{fmtQtd(c.qtde)} {c.unidade}</div>
                          <div className="w-32 text-right font-black text-slate-900 text-sm">
                            {modoFaturamento === 'venda_direta' && exibicaoMateriais === 'sem_preco'
                              ? null
                              : precoComplemento(c) > 0
                                ? `R$ ${fmt(precoComplemento(c) * (parseFloat(c.qtde) || 1) * (modoFaturamento === 'empreitada' ? cf.fatorMateriais : 1))}`
                                : <span className="text-slate-400 font-normal italic text-xs">A cotação</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Bloco de investimento */}
            <div>
              <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4 border-b border-slate-100 pb-2">Investimento</h4>
              {modoFaturamento === 'venda_direta' ? (
                <div className="space-y-3">
                  {exibicaoMateriais === 'resumo' && (
                    <div className="flex justify-between items-center py-2 border-b border-slate-50">
                      <div>
                        <p className="font-bold text-slate-800 text-sm">Cj. materiais de refrigeração e isolamento</p>
                        <p className="text-[10px] text-slate-400">Faturamento direto ao fornecedor</p>
                      </div>
                      <p className="font-black text-slate-900">R$ {fmt(cf.custo_materiais)}</p>
                    </div>
                  )}
                  {exibicaoMateriais === 'itemizado' && cf.blocosMateriais.map((b, i) => (
                    <div key={`m${i}`} className="flex justify-between items-center py-2 border-b border-slate-50">
                      <div>
                        <p className={`flex items-center gap-2 font-bold text-sm ${corDoBloco(b.nome).texto}`}>
                          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${corDoBloco(b.nome).dot}`} />
                          {b.nome}
                        </p>
                        <p className="text-[10px] text-slate-400 pl-4">Faturamento direto ao fornecedor — valor de cotação</p>
                      </div>
                      <p className="font-black text-slate-900">R$ {fmt(b.valor)}</p>
                    </div>
                  ))}
                  {(exibicaoMateriais === 'resumo' || apresentacao === 'blocos') ? (
                    cf.blocosServicos.map((b, i) => (
                      <div key={`s${i}`} className="flex justify-between items-center py-2 border-b border-slate-50">
                        <p className={`flex items-center gap-2 font-bold text-sm ${COR_MAO_DE_OBRA.texto}`}>
                          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${COR_MAO_DE_OBRA.dot}`} />
                          {b.nome}
                        </p>
                        <p className="font-black text-slate-900">R$ {fmt(b.valor)}</p>
                      </div>
                    ))
                  ) : (
                    <div className="flex justify-between items-center py-2 border-b border-slate-50">
                      <p className={`flex items-center gap-2 font-bold text-sm ${COR_MAO_DE_OBRA.texto}`}>
                        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${COR_MAO_DE_OBRA.dot}`} />
                        Instalação, mobilização e comissionamento
                      </p>
                      <p className="font-black text-slate-900">R$ {fmt(cf.preco_servicos_cliente)}</p>
                    </div>
                  )}
                </div>
              ) : apresentacao === 'blocos' ? (
                <div className="space-y-3">
                  {cf.blocosCliente.map((b, i) => (
                    <div key={i} className="flex justify-between items-center py-2 border-b border-slate-50">
                      <p className="font-bold text-slate-800 text-sm">{b.nome}</p>
                      <p className="font-black text-slate-900">R$ {fmt(b.valor)}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex justify-between items-center py-4 bg-slate-50 rounded-xl px-5 border border-slate-200">
                  <div>
                    <p className="font-bold text-slate-800">Fornecimento e instalação completos</p>
                    {modoFaturamento === 'venda_direta' && <p className="text-xs text-slate-500">Materiais com faturamento direto ao cliente pelo fornecedor</p>}
                  </div>
                  <p className="font-black text-slate-900 text-lg">R$ {fmt(modoFaturamento === 'venda_direta' ? cf.preco_servicos_cliente : cf.preco_venda)}</p>
                </div>
              )}
            </div>

            {/* Total geral */}
            <div className="pt-6 border-t-4 border-slate-900 flex flex-col md:flex-row justify-between items-center gap-6">
              <p className="text-slate-400 text-xs max-w-xs leading-relaxed print:text-[8px]">
                {modoFaturamento === 'venda_direta'
                  ? (exibicaoMateriais === 'sem_preco'
                      ? '* Materiais e equipamentos serão faturados diretamente pelo fornecedor ao cliente. O valor indicado refere-se aos serviços de instalação.'
                      : '* Materiais e equipamentos faturados diretamente pelo fornecedor ao cliente, pelos valores de cotação, sem margem. Serviços de instalação faturados pelo instalador.')
                  : `* Proposta válida até ${new Date(Date.now() + (parseInt(cond.validade_dias) || 10) * 86400000).toLocaleDateString('pt-BR')}. Preços sujeitos a alteração após este prazo.`}
                {modoFaturamento !== 'venda_direta' && complementosPreenchidos.some(c => precoComplemento(c) <= 0) && ' Itens "a cotação" não incluídos no total.'}
              </p>
              <div className="text-right">
                <div className="text-slate-500 text-sm font-bold uppercase">Investimento Total</div>
                <div className="text-4xl font-black text-indigo-600">
                  R$ {fmt(modoFaturamento === 'venda_direta' && exibicaoMateriais === 'sem_preco' ? cf.preco_servicos_cliente : cf.preco_venda)}
                </div>
              </div>
            </div>

            {/* Condições comerciais */}
            <div className="bg-slate-50 rounded-xl border border-slate-200 p-6">
              <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">Condições Comerciais</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  { l: 'Condições de Pagamento', v: cond.pagamento },
                  { l: 'Prazo de Execução', v: cond.prazo_execucao },
                  { l: 'Garantia', v: cond.garantia },
                  { l: 'Validade da Proposta', v: `${cond.validade_dias} dias úteis a partir da emissão` },
                ].map(r => r.v && (
                  <div key={r.l}>
                    <p className="text-[9px] font-black text-slate-400 uppercase mb-0.5">{r.l}</p>
                    <p className="text-xs text-slate-700 leading-relaxed">{r.v}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Aceite */}
            <div className="pt-4 border-t border-slate-200">
              <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-6">Aprovação e Aceite</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                <div className="space-y-1">
                  <div className="h-px bg-slate-900 w-full mt-8" />
                  <p className="text-xs font-bold text-slate-700 mt-1">{dadosCliente.nome || 'Cliente'}</p>
                  <p className="text-[9px] text-slate-400">Aprovação do cliente</p>
                </div>
                <div className="space-y-1">
                  <div className="h-px bg-slate-900 w-full mt-8" />
                  <p className="text-xs font-bold text-slate-700 mt-1">Prestador de Serviços</p>
                  <p className="text-[9px] text-slate-400">Data: _____ / _____ / _________</p>
                </div>
              </div>
            </div>

          </div>

          {/* Ações */}
          <div className="bg-slate-50 p-6 border-t border-slate-100 flex justify-center gap-4 print:hidden">
            <button onClick={() => window.print()} className="px-6 py-2 bg-slate-200 text-slate-700 rounded-lg font-bold hover:bg-slate-300 transition-all">Imprimir 🖨️</button>
            <div className="flex flex-col items-center gap-1">
              <button onClick={gerarPDF} disabled={loading} className={`px-6 py-2 text-white rounded-lg font-bold transition-all disabled:bg-slate-300 ${
                estaDesatualizada('proposta') ? 'bg-amber-600 hover:bg-amber-700 ring-2 ring-amber-300' : 'bg-indigo-600 hover:bg-indigo-700'}`}>
                {loading ? 'Gerando...' : (estaDesatualizada('proposta') ? '🔄 Atualizar PDF' : 'Baixar PDF 📥')}
              </button>
              <SeloStale tipo="proposta" texto="⚠️ PDF desatualizado — regere" />
            </div>
            <button onClick={enviarWhatsApp} className="px-6 py-2 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 transition-all">WhatsApp 💬</button>
          </div>

          {/* Aviso de salvar */}
          {(onSalvarProjeto || onSalvarComo) && (
            <div className="px-6 pb-6 print:hidden">
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-bold text-blue-800">
                    {projetoAtual?.id ? '💾 Projeto atualizado — grave para preservar as alterações' : '💾 Salve o projeto para preservar este dimensionamento'}
                  </p>
                  <p className="text-xs text-blue-600 mt-0.5">
                    {projetoAtual?.id
                      ? 'Use "Salvar" para substituir o existente ou "Salvar Como" para criar uma nova versão.'
                      : 'Use o botão Salvar no topo da tela para guardar este projeto.'}
                  </p>
                </div>
                {projetoAtual?.id && (
                  <div className="flex gap-2 flex-shrink-0">
                    {onSalvarProjeto && (
                      <button onClick={onSalvarProjeto}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-sm transition-all">
                        💾 Salvar
                      </button>
                    )}
                    {onSalvarComo && (
                      <button onClick={onSalvarComo}
                        className="px-4 py-2 bg-white border border-blue-300 hover:bg-blue-50 text-blue-700 rounded-lg font-bold text-sm transition-all">
                        Salvar Como
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GeradorOrcamento;
