import React, { useState, useEffect, useRef } from 'react';
import api from './api';
import { useAuth } from './contexts/AuthContext';
import LoginPage from './pages/LoginPage';

// --- IMPORTAÇÕES ---
import CalculadoraGabinete from './components/CalculadoraGabinete.jsx';
import CalculadoraCargaTermica from './components/CalculadoraCargaTermica.jsx';
import SelecaoEquipamentos from './components/SelecaoEquipamentos.jsx';
import ComponentesFluxo from './components/ComponentesFluxo.jsx';
import ConfiguracoesPage from './components/ConfiguracoesPage.jsx';
import CalculadoraTubulacao from './components/CalculadoraTubulacao.jsx';
import GeradorOrcamento from './components/GeradorOrcamento.jsx';
import PainelResumoLateral from './components/PainelResumoLateral.jsx';
import PainelInsights from './components/PainelInsights.jsx';
import PainelCotacoes from './components/PainelCotacoes.jsx';
import EtapaCard from './components/EtapaCard.jsx';
import { Button } from './components/ui/button.jsx';
import { Badge } from './components/ui/badge.jsx';
import { Separator } from './components/ui/separator.jsx';
import { LayoutDashboard, FolderOpen, Settings, LogOut, Plus, Save, CopyPlus, CheckCircle2, Circle, Lock, ChevronRight } from 'lucide-react';


function AppContent({ catalogo }) {
  const { user, logout } = useAuth();
  const [dadosDoGabinete, setDadosDoGabinete] = useState(null);
  const [gabineteCalculado, setGabineteCalculado] = useState(false);
  const gabineteCalculadoRef = React.useRef(false); // rastreia transição false→true
  const [projetoKey, setProjetoKey] = useState(0); // força remount dos componentes ao novo projeto
  const [deltaTCalculado, setDeltaTCalculado] = useState(null);
  const [cargaCalculada, setCargaCalculada] = useState(null);
  const [itensOrcamento, setItensOrcamento] = useState({ materiais: [], equipamentos: [] });
  const [tempExternaCalculo, setTempExternaCalculo] = useState(35); // T.Amb do Card 2
  const [itensGabinete,   setItensGabinete]   = useState([]);   // step 1 — lista de corte de painéis
  const [itensAcessorios, setItensAcessorios] = useState([]);   // step 5 — componentes de fluxo
  const [itensTubulacao,  setItensTubulacao]  = useState([]);   // step 4 — tubulação
  const [resultadoTubulacao, setResultadoTubulacao] = useState(null); // resultado completo do Card 4 (bitolas, distância)
  const [configuracoesMontagem, setConfiguracoesMontagem] = useState({
    tipo_filtro:       'solda',
    tipo_visor:        'solda',
    trecho_vet_evap:   0.5,
    trecho_evap_sifao: 0.5,
    trecho_subida:     1.0,
    trecho_sifao_gbc:  0.5,
  });
  const [passoAtual, setPassoAtual] = useState(1);
  const [passoExpandido, setPassoExpandido] = useState(1);
  const [passoSelecionado, setPassoSelecionado] = useState(1);
  const [proximaEtapa, setProximaEtapa] = useState(null); // {numero, label} — aguardando confirmação do usuário
  const [salvando, setSalvando] = useState(false);
  const [projetoAtual, setProjetoAtual] = useState(null); // { id, nome, cliente } ou null se novo
  const [listaProjetos, setListaProjetos] = useState([]);
  const [mostrandoHistorico, setMostrandoHistorico] = useState(false);
  const [mostrandoCotacoes, setMostrandoCotacoes] = useState(false);
  const [mostrandoConfiguracoes, setMostrandoConfiguracoes] = useState(false);

  // --- FUNÇÕES DE INTERLIGAÇÃO (PONTES) ---
  const { useCallback, useEffect } = React;

  // Carrega perfil de montagem ativo no boot
  useEffect(() => {
    api.get('/api/v1/configuracoes/montagem').then(r => {
      const ativo = r.data.find(p => p.ativo) || r.data[0];
      if (ativo) {
        setConfiguracoesMontagem({
          tipo_filtro:       ativo.tipo_filtro,
          tipo_visor:        ativo.tipo_visor,
          trecho_vet_evap:   parseFloat(ativo.trecho_vet_evap),
          trecho_evap_sifao: parseFloat(ativo.trecho_evap_sifao),
          trecho_subida:     parseFloat(ativo.trecho_subida),
          trecho_sifao_gbc:  parseFloat(ativo.trecho_sifao_gbc),
        });
      }
    }).catch(() => {});
  }, []);

  // Reconstrói materiais do orçamento sempre que qualquer fonte muda.
  // Ordem: gabinete (painéis) → acessórios (VET, separador) → tubulação (tubos, isolamento)
  useEffect(() => {
    setItensOrcamento(prev => ({
      ...prev,
      materiais: [...itensGabinete, ...itensAcessorios, ...itensTubulacao],
    }));
  }, [itensGabinete, itensAcessorios, itensTubulacao]);

  // 1. Recebe do Gabinete (Módulo 1)
  const receberDadosGabinete = useCallback((dadosCompletos) => {
    console.log("Recebido do Gabinete:", dadosCompletos);

    if (!dadosCompletos) {
      setDadosDoGabinete(null);
      setGabineteCalculado(false);
      return;
    }

    // Passa dimensões para a Carga Térmica
    setDadosDoGabinete({
      comprimento: dadosCompletos.comprimento,
      largura: dadosCompletos.largura,
      altura: dadosCompletos.altura,
      temperatura_interna: dadosCompletos.temperatura_interna,
      espessura: dadosCompletos.espessura,
      nucleo: dadosCompletos.nucleo,
      tipo_piso: dadosCompletos.tipo_piso,
      imagem_projeto: dadosCompletos.imagem_projeto
    });

    // Marca que o gabinete foi calculado (lista_corte vem só após clicar Calcular)
    // Scroll apenas na transição false → true (não a cada edição)
    if (dadosCompletos.lista_corte) {
      const eraFalse = !gabineteCalculadoRef.current;
      gabineteCalculadoRef.current = true;
      setGabineteCalculado(true);
      if (eraFalse) {
        setPassoSelecionado(2);
        setProximaEtapa({ numero: 2, label: 'Cálculo de Carga Térmica' });
      }
    } else {
      gabineteCalculadoRef.current = false;
      setGabineteCalculado(false);
      setProximaEtapa(null);
      setPassoExpandido(1); setPassoSelecionado(1);
    }

    if (dadosCompletos.lista_materiais) {
      setItensGabinete(dadosCompletos.lista_materiais); // painéis, acessórios de montagem etc.
      setItensOrcamento(prev => ({ ...prev, imagem_projeto: dadosCompletos.imagem_projeto }));
    } else if (dadosCompletos.imagem_projeto) {
      setItensOrcamento(prev => ({ ...prev, imagem_projeto: dadosCompletos.imagem_projeto }));
    }
    
    setPassoAtual(prev => (prev < 2 ? 2 : prev));
  }, []);

  // 2. Recebe da Carga Térmica (Módulo 2)
  const receberResultadoCarga = useCallback((valorKcal, tempExt) => {
    setCargaCalculada(valorKcal);
    if (tempExt) setTempExternaCalculo(tempExt); // guarda T.Amb do Card 2
    setPassoAtual(prev => Math.max(prev, 3));
    setPassoSelecionado(3);
    setProximaEtapa({ numero: 3, label: 'Seleção de Equipamentos' });
  }, []);

  const receberEquipamentosFinalizados = useCallback((equipamentos) => {
    setItensOrcamento(prev => ({ ...prev, equipamentos }));
    setItensAcessorios([]);
    setItensTubulacao([]);
    setPassoAtual(prev => Math.max(prev, 4));
    setPassoSelecionado(4);
    setProximaEtapa({ numero: 4, label: 'Dimensionamento de Tubulação' });
  }, []);

  const receberDadosTubulacao = useCallback((listaTubos, resultadoCompleto) => {
    setItensTubulacao(listaTubos);
    if (resultadoCompleto) setResultadoTubulacao(resultadoCompleto);
    setPassoAtual(prev => Math.max(prev, 5));
    setPassoSelecionado(5);
    setProximaEtapa({ numero: 5, label: 'Componentes e Acessórios' });
  }, []);

  const receberComponentesFluxo = useCallback((listaAcessorios) => {
    setItensAcessorios(listaAcessorios);
    setPassoAtual(prev => Math.max(prev, 6));
    setPassoSelecionado(6);
    setProximaEtapa({ numero: 6, label: 'Gerador de Orçamento' });
  }, []);

  // ── Wizard helpers ────────────────────────────────────────────────────
  const etapaDisponivel = (n) => ({
    1: true,
    2: gabineteCalculado,
    3: cargaCalculada != null,
    4: itensOrcamento.equipamentos.length > 0,
    5: passoAtual >= 5,  // desbloqueado após tubulação
    6: itensOrcamento.materiais.length > 0 || itensOrcamento.equipamentos.length > 0,
  }[n] ?? false);

  const etapaConcluida = (n) => ({
    1: gabineteCalculado,
    2: cargaCalculada != null,
    3: itensOrcamento.equipamentos.length > 0,
    4: passoAtual >= 5,  // tubulação concluída
    5: passoAtual >= 6,  // componentes concluídos
    6: false,
  }[n] ?? false);

  const statusEtapa = (n) => {
    if (!etapaDisponivel(n)) return 'bloqueado';
    if (etapaConcluida(n))   return 'concluido';
    return 'disponivel'; // acessível mas ainda não concluída
  };

  // Clique no header → só seleciona (mostra detalhe à direita, NÃO abre para edição)
  const selecionarEtapa = (n) => { if (etapaDisponivel(n)) setPassoSelecionado(n); };

  // Clique em "Editar" → abre para edição e seleciona
  const editarEtapa = (n) => {
    if (etapaDisponivel(n)) {
      setPassoExpandido(n);
      setPassoSelecionado(n);
      setProximaEtapa(null); // cancela confirmação pendente ao editar
    }
  };

  // Clique em "Descartar edição" → fecha sem perder dados, mantém selecionado
  const fecharEtapa = () => { setPassoExpandido(null); setProximaEtapa(null); };

  // Confirmação do usuário para avançar à próxima etapa
  const confirmarAvanco = () => {
    if (proximaEtapa) {
      setPassoExpandido(proximaEtapa.numero);
      setPassoSelecionado(proximaEtapa.numero);
      setProximaEtapa(null);
    }
  };
  const recusarAvanco = () => setProximaEtapa(null);

  // Summaries exibidos nos cards colapsados
  const resumoEtapa = (n) => {
    if (n === 1 && dadosDoGabinete)
      return `${dadosDoGabinete.comprimento}×${dadosDoGabinete.largura}×${dadosDoGabinete.altura}m | ${dadosDoGabinete.nucleo} ${dadosDoGabinete.espessura}mm | ${dadosDoGabinete.temperatura_interna}°C`;
    if (n === 2 && cargaCalculada)
      return `${Number(cargaCalculada).toLocaleString('pt-BR')} kcal/h requeridos`;
    if (n === 3 && itensOrcamento.equipamentos.length > 0)
      return `${itensOrcamento.equipamentos.length} equipamento(s) selecionado(s)`;
    if (n === 4 && passoAtual >= 5)
      return 'Tubulação dimensionada';
    if (n === 5 && passoAtual >= 6)
      return 'Acessórios e componentes confirmados';
    return null;
  };

  const getUltimoEquipamento = () => {
    const lista = itensOrcamento.equipamentos;
    if (lista.length === 0) return null;
    const ultimo = { ...lista[lista.length - 1] };
    return ultimo;
  };

  const getEvaporador = () => {
    const lista = itensOrcamento.equipamentos;
    return lista.findLast(e => e.categoria === 'Evaporadora') ?? null;
  };

  const getCondensadora = () => {
    const lista = itensOrcamento.equipamentos;
    return lista.findLast(e => e.categoria === 'Unidade Condensadora') ?? null;
  };

  const removerEquipamentoSugerido = (indexParaRemover) => {
    setItensOrcamento(prev => ({
      ...prev,
      equipamentos: prev.equipamentos.filter((_, index) => index !== indexParaRemover)
    }));
  };

  const novoProjeto = () => {
    if (!window.confirm("Iniciar novo projeto? Os dados não salvos serão perdidos.")) return;
    // Reseta TODOS os estados do App
    setDadosDoGabinete(null);
    setCargaCalculada(null);
    setItensOrcamento({ materiais: [], equipamentos: [] });
    setItensGabinete([]);
    setItensAcessorios([]);
    setItensTubulacao([]);
    setResultadoTubulacao(null);
    setConfiguracoesMontagem({
      tipo_filtro: 'solda', tipo_visor: 'solda',
      trecho_vet_evap: 0.5, trecho_evap_sifao: 0.5,
      trecho_subida: 1.0, trecho_sifao_gbc: 0.5,
    });
    setPassoAtual(1);
    setProjetoAtual(null);
    setGabineteCalculado(false);
    setDeltaTCalculado(null);
    setTempExternaCalculo(35);   // reset T.Amb
    setProximaEtapa(null);       // reset confirmação pendente
    gabineteCalculadoRef.current = false;
    // projetoKey incrementado remonta TODOS os cards (key propagada)
    setProjetoKey(k => k + 1);
    setPassoExpandido(1); setPassoSelecionado(1);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const _montarPayload = (nome, cliente) => ({
    nome,
    cliente: cliente || 'Cliente Avulso',
    dados_completos: {
      gabinete: dadosDoGabinete,
      carga_termica: cargaCalculada,
      orcamento: itensOrcamento,
      configuracoes: { passo_atual: passoAtual }
    }
  });

  const salvarProjeto = async () => {
    if (!dadosDoGabinete) {
      alert("Inicie um projeto antes de salvar.");
      return;
    }

    // Projeto novo: pede nome antes de salvar
    if (!projetoAtual) {
      const nome = window.prompt("Digite um nome para o projeto:", "Novo Projeto de Refrigeração");
      if (!nome) return;
      setSalvando(true);
      try {
        const resp = await api.post('/api/v1/projetos', _montarPayload(nome));
        setProjetoAtual({ id: resp.data.id, nome: resp.data.nome, cliente: resp.data.cliente });
        alert("Projeto salvo com sucesso!");
        if (mostrandoHistorico) abrirHistorico();
      } catch { alert("Erro ao salvar o projeto."); }
      finally { setSalvando(false); }
      return;
    }

    // Projeto existente: atualiza com dados originais
    setSalvando(true);
    try {
      await api.patch(`/api/v1/projetos/${projetoAtual.id}`, _montarPayload(projetoAtual.nome, projetoAtual.cliente));
      alert("Projeto atualizado com sucesso!");
      if (mostrandoHistorico) abrirHistorico();
    } catch { alert("Erro ao salvar o projeto."); }
    finally { setSalvando(false); }
  };

  const salvarComo = async () => {
    if (!dadosDoGabinete) {
      alert("Inicie um projeto antes de salvar.");
      return;
    }
    const sugestao = projetoAtual ? `${projetoAtual.nome} (cópia)` : "Novo Projeto de Refrigeração";
    const nome = window.prompt("Digite um nome para o novo projeto:", sugestao);
    if (!nome) return;
    setSalvando(true);
    try {
      const resp = await api.post('/api/v1/projetos', _montarPayload(nome, projetoAtual?.cliente));
      setProjetoAtual({ id: resp.data.id, nome: resp.data.nome, cliente: resp.data.cliente });
      alert(`Projeto salvo como "${nome}"!`);
      if (mostrandoHistorico) abrirHistorico();
    } catch { alert("Erro ao salvar o projeto."); }
    finally { setSalvando(false); }
  };

  const abrirHistorico = async () => {
    try {
      const resp = await api.get('/api/v1/projetos');
      setListaProjetos(resp.data);
      setMostrandoHistorico(true);
    } catch (error) {
      alert("Erro ao carregar histórico.");
    }
  };

  const carregarProjeto = (projeto) => {
    const d = projeto.dados_completos;
    if (d.gabinete) setDadosDoGabinete(d.gabinete);
    if (d.carga_termica) setCargaCalculada(d.carga_termica);
    if (d.orcamento) setItensOrcamento(d.orcamento);
    if (d.configuracoes?.passo_atual) setPassoAtual(d.configuracoes.passo_atual);
    setProjetoAtual({ id: projeto.id, nome: projeto.nome, cliente: projeto.cliente });
    setMostrandoHistorico(false);
    alert(`Projeto "${projeto.nome}" carregado com sucesso!`);
  };

  return (
    <div className="h-screen bg-background flex flex-col overflow-hidden print:bg-white print:h-auto print:overflow-visible">

      {/* ══ BARRA DE CABEÇALHO ÚNICA — alinha as 3 colunas ══ */}
      <div className="sticky top-0 z-20 flex border-b bg-card print:hidden">

        {/* Cabeçalho Esquerda */}
        <div className="w-60 flex-shrink-0 border-r hidden lg:flex flex-col justify-center px-5 py-3">
          <img
            src="/logoIceNexusIAR _png.png"
            alt="IceNexus IAR"
            className="w-full max-h-12 object-contain"
          />
          <p className="text-[9px] font-semibold text-muted-foreground uppercase tracking-widest text-center mt-1">
            Engineering Suite <span className="text-muted-foreground/40 ml-1">v1.2</span>
          </p>
        </div>

        {/* Cabeçalho Centro */}
        <div className="flex-1 flex flex-col justify-between px-6 py-3">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="font-semibold text-foreground leading-tight">
                {projetoAtual ? projetoAtual.nome : 'Novo Dimensionamento'}
              </h2>
              <div className="mt-0.5">
                {projetoAtual
                  ? <span className="text-xs text-muted-foreground">
                      {projetoAtual.cliente ? `Cliente: ${projetoAtual.cliente}` : '✅ Salvo'}
                    </span>
                  : <Badge variant="warning" className="text-[10px]">Não salvo</Badge>
                }
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={novoProjeto} className="gap-1">
                <Plus className="w-4 h-4" /> Novo
              </Button>
              <Button variant="outline" size="sm" onClick={salvarComo} disabled={salvando} className="gap-1">
                <CopyPlus className="w-4 h-4" /> Salvar Como
              </Button>
              <Button size="sm" onClick={salvarProjeto} disabled={salvando} className="gap-1">
                <Save className="w-4 h-4" /> {salvando ? 'Salvando...' : 'Salvar'}
              </Button>
              <Separator orientation="vertical" className="h-6 mx-1" />
              <span className="text-xs text-muted-foreground hidden sm:block">{user.username}</span>
              <Button variant="ghost" size="icon" onClick={logout} title="Sair" className="text-muted-foreground hover:text-destructive">
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          </div>
          {/* Progress tracker */}
          <div className="mt-2">
            <div className="flex items-center gap-1">
              {[
                [1,'Gabinete'], [2,'Carga'], [3,'Equipamentos'],
                [4,'Acessórios'], [5,'Tubulação'], [6,'Orçamento']
              ].map(([step, label], idx) => {
                const st        = statusEtapa(step);
                const concluido = st === 'concluido';
                const ativo     = passoExpandido === step;
                const disponivel= st !== 'bloqueado';
                return (
                  <React.Fragment key={step}>
                    {idx > 0 && (
                      <div className={`flex-1 h-px transition-colors ${concluido || ativo ? 'bg-primary/40' : 'bg-border'}`} />
                    )}
                    <div
                      className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium transition-all
                        ${disponivel ? 'cursor-pointer' : 'cursor-not-allowed'}
                        ${ativo ? 'bg-primary text-primary-foreground' : ''}
                        ${concluido && !ativo ? 'text-emerald-600 hover:bg-muted' : ''}
                        ${!concluido && !ativo ? 'text-muted-foreground' : ''}
                      `}
                      onClick={() => abrirEtapa(step)}
                    >
                      {ativo        ? <Circle className="w-3 h-3 fill-current" />
                      : concluido   ? <CheckCircle2 className="w-3 h-3" />
                      : !disponivel ? <Lock className="w-3 h-3" />
                      : <Circle className="w-3 h-3" />}
                      <span className="hidden sm:block">{label}</span>
                      <span className="sm:hidden">{step}</span>
                    </div>
                  </React.Fragment>
                );
              })}
            </div>
          </div>
        </div>

        {/* Cabeçalho Direita */}
        <div className="w-80 flex-shrink-0 border-l hidden xl:flex flex-col justify-center px-5 py-3"
             style={{ background: 'linear-gradient(135deg, #1a0d2e 0%, #2a1245 100%)' }}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-black text-white uppercase tracking-widest">Painel Técnico</h3>
              <p className="text-xs text-purple-300/70 font-bold uppercase mt-0.5">Indicadores em tempo real</p>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse flex-shrink-0" />
              <span className="text-[10px] text-emerald-400 font-medium">Conectado</span>
            </div>
          </div>
        </div>
      </div>

      {/* ══ CORPO — 3 colunas abaixo do header ══ */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

      {/* ── Sidebar Esquerda ── */}
      <aside className="w-60 border-r bg-card flex-shrink-0 hidden lg:flex flex-col print:hidden overflow-y-auto">

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1">
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-primary/10 text-primary font-semibold text-sm cursor-pointer">
            <LayoutDashboard className="w-4 h-4" /> Projeto Atual
          </div>
          <div onClick={abrirHistorico}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground text-sm cursor-pointer transition-colors">
            <FolderOpen className="w-4 h-4" /> Histórico
          </div>
          <div onClick={() => setMostrandoCotacoes(true)}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground text-sm cursor-pointer transition-colors">
            <CopyPlus className="w-4 h-4" /> Cotações
          </div>
          <div onClick={() => setMostrandoConfiguracoes(true)}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground text-sm cursor-pointer transition-colors">
            <Settings className="w-4 h-4" /> Configurações
          </div>
        </nav>

        {/* Insights */}
        {dadosDoGabinete && (
          <div className="px-3 pb-2">
            <Separator className="mb-3" />
            <PainelInsights
              dimensoes={{ comp: dadosDoGabinete.comprimento, larg: dadosDoGabinete.largura, alt: dadosDoGabinete.altura }}
              temps={{ interna: dadosDoGabinete.temperatura_interna, externa: 35,
                evap: deltaTCalculado != null ? parseFloat(dadosDoGabinete.temperatura_interna) - parseFloat(deltaTCalculado) : NaN }}
              isolamento={{ esp: dadosDoGabinete.espessura, nuc: dadosDoGabinete.nucleo }}
              cargaCalculada={cargaCalculada}
              produto={null}
              compacto={true}
            />
          </div>
        )}

        {/* Versão */}
        <div className="px-4 py-3 border-t border-border mt-auto">
          <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Versão</p>
          <p className="text-[11px] font-black text-foreground">v2.1 — Jun 2026</p>
          <p className="text-[9px] text-muted-foreground mt-0.5">Tubulação ASHRAE · Modo Eng.</p>
        </div>

      </aside>

      {/* ── Área Principal ── */}
      <main className="flex-1 min-w-0 min-h-0 overflow-y-auto print:overflow-visible">

        <div className="p-6 max-w-4xl mx-auto w-full space-y-4 print:p-0 print:max-w-none print:m-0">
          
          {/* PAINEL DE COTAÇÕES */}
          <PainelCotacoes aberto={mostrandoCotacoes} aoFechar={() => setMostrandoCotacoes(false)} />

          {/* MODAL CONFIGURAÇÕES DE MONTAGEM */}
          {mostrandoConfiguracoes && (
            <ConfiguracoesPage
              onFechar={() => setMostrandoConfiguracoes(false)}
              onPerfilAtivo={(perfil) => setConfiguracoesMontagem({
                tipo_filtro:       perfil.tipo_filtro,
                tipo_visor:        perfil.tipo_visor,
                trecho_vet_evap:   parseFloat(perfil.trecho_vet_evap),
                trecho_evap_sifao: parseFloat(perfil.trecho_evap_sifao),
                trecho_subida:     parseFloat(perfil.trecho_subida),
                trecho_sifao_gbc:  parseFloat(perfil.trecho_sifao_gbc),
              })}
            />
          )}

          {/* MODAL DE HISTÓRICO */}
          {mostrandoHistorico && (
            <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-300 print:hidden">
              <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
                <div className="bg-slate-900 p-6 flex justify-between items-center text-white">
                  <div>
                    <h3 className="text-xl font-bold">Histórico de Projetos</h3>
                    <p className="text-slate-400 text-xs uppercase font-bold tracking-widest mt-1">Engenharia v0.1</p>
                  </div>
                  <button onClick={() => setMostrandoHistorico(false)} className="w-10 h-10 rounded-full hover:bg-white/10 flex items-center justify-center text-2xl">✕</button>
                </div>
                
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                  {listaProjetos.length === 0 ? (
                    <div className="text-center py-12 text-slate-400">Nenhum projeto encontrado.</div>
                  ) : (
                    listaProjetos.map((proj) => (
                      <div key={proj.id} className="group p-4 bg-slate-50 border border-slate-200 rounded-xl hover:border-blue-400 hover:bg-blue-50 transition-all flex justify-between items-center">
                        <div>
                          <div className="font-bold text-slate-800 group-hover:text-blue-700">{proj.nome}</div>
                          <div className="text-[10px] text-slate-500 font-bold uppercase mt-1">
                            {new Date(proj.data_criacao).toLocaleDateString('pt-BR')} | {proj.cliente}
                          </div>
                        </div>
                        <button 
                          onClick={() => carregarProjeto(proj)}
                          className="bg-white border border-slate-200 px-4 py-2 rounded-lg text-xs font-black text-slate-600 hover:bg-blue-600 hover:text-white hover:border-blue-600 transition-all shadow-sm"
                        >
                          ABRIR 📂
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* O Progress Tracker antigo foi removido daqui e movido para o header */}

          {/* ── WIZARD — 6 etapas colapsáveis ── */}
          <div className="space-y-4 print:hidden">

            {/* 1. Gabinete */}
            <EtapaCard
              numero={1} titulo="Configuração do Gabinete" icone="📏"
              status={statusEtapa(1)} resumo={resumoEtapa(1)}
              expandido={passoExpandido === 1}
              selecionado={passoSelecionado === 1 && passoExpandido !== 1}
              onSelecionar={() => selecionarEtapa(1)}
              onEditar={() => editarEtapa(1)} onFechar={fecharEtapa}
              confirmacaoProxima={passoExpandido === 1 && proximaEtapa ? proximaEtapa.label : null}
              onConfirmar={confirmarAvanco} onRecusar={recusarAvanco}
            >
              <CalculadoraGabinete
                key={projetoKey}
                aoFinalizar={receberDadosGabinete}
                fabricantes={catalogo.fabricantes}
                portasCatalogo={catalogo.portasCatalogo}
              />
            </EtapaCard>

            {/* 2. Carga Térmica */}
            <EtapaCard
              numero={2} titulo="Cálculo de Carga Térmica" icone="❄️"
              status={statusEtapa(2)} resumo={resumoEtapa(2)}
              expandido={passoExpandido === 2}
              selecionado={passoSelecionado === 2 && passoExpandido !== 2}
              onSelecionar={() => selecionarEtapa(2)}
              onEditar={() => editarEtapa(2)} onFechar={fecharEtapa}
              confirmacaoProxima={passoExpandido === 2 && proximaEtapa ? proximaEtapa.label : null}
              onConfirmar={confirmarAvanco} onRecusar={recusarAvanco}
            >
              <CalculadoraCargaTermica key={projetoKey} dadosIniciais={dadosDoGabinete} aoFinalizar={receberResultadoCarga} />
            </EtapaCard>

            {/* 3. Seleção de Equipamentos */}
            <EtapaCard
              numero={3} titulo="Seleção de Equipamentos" icone="⚙️"
              status={statusEtapa(3)} resumo={resumoEtapa(3)}
              expandido={passoExpandido === 3}
              selecionado={passoSelecionado === 3 && passoExpandido !== 3}
              onSelecionar={() => selecionarEtapa(3)}
              onEditar={() => editarEtapa(3)} onFechar={fecharEtapa}
              confirmacaoProxima={passoExpandido === 3 && proximaEtapa ? proximaEtapa.label : null}
              onConfirmar={confirmarAvanco} onRecusar={recusarAvanco}
            >
              <SelecaoEquipamentos
                key={projetoKey}
                cargaInicial={cargaCalculada}
                tempInterna={dadosDoGabinete?.temperatura_interna}
                tempAmb={tempExternaCalculo}
                onDeltaTChange={setDeltaTCalculado}
                aoFinalizar={receberEquipamentosFinalizados}
              />
            </EtapaCard>

            {/* 4. Tubulação */}
            <EtapaCard
              numero={4} titulo="Dimensionamento de Tubulação" icone="🔩"
              status={statusEtapa(4)} resumo={resumoEtapa(4)}
              expandido={passoExpandido === 4}
              selecionado={passoSelecionado === 4 && passoExpandido !== 4}
              onSelecionar={() => selecionarEtapa(4)}
              onEditar={() => editarEtapa(4)} onFechar={fecharEtapa}
              confirmacaoProxima={passoExpandido === 4 && proximaEtapa ? proximaEtapa.label : null}
              onConfirmar={confirmarAvanco} onRecusar={recusarAvanco}
            >
              <CalculadoraTubulacao key={projetoKey} evaporador={getEvaporador()} condensadora={getCondensadora()} aoFinalizar={receberDadosTubulacao} />
            </EtapaCard>

            {/* 5. Componentes e Acessórios */}
            <EtapaCard
              numero={5} titulo="Componentes e Acessórios" icone="🔧"
              status={statusEtapa(5)} resumo={resumoEtapa(5)}
              expandido={passoExpandido === 5}
              selecionado={passoSelecionado === 5 && passoExpandido !== 5}
              onSelecionar={() => selecionarEtapa(5)}
              onEditar={() => editarEtapa(5)} onFechar={fecharEtapa}
              confirmacaoProxima={passoExpandido === 5 && proximaEtapa ? proximaEtapa.label : null}
              onConfirmar={confirmarAvanco} onRecusar={recusarAvanco}
            >
              <ComponentesFluxo
                key={projetoKey}
                cargaAlvo={getUltimoEquipamento()?.capacidade_real || cargaCalculada}
                fluido={getUltimoEquipamento()?.fluido || 'R404A'}
                tempEvap={getUltimoEquipamento()?.temp_evap || -10}
                tempAmb={tempExternaCalculo}
                evaporador={getEvaporador()}
                condensadora={getCondensadora()}
                dadosTubulacao={resultadoTubulacao}
                configuracoesMontagem={configuracoesMontagem}
                aoFinalizar={receberComponentesFluxo}
              />
            </EtapaCard>

            {/* 6. Orçamento */}
            <EtapaCard
              numero={6} titulo="Gerador de Orçamento" icone="💰"
              status={statusEtapa(6)} resumo={resumoEtapa(6)}
              somenteLeitura
              expandido={passoExpandido === 6}
              selecionado={passoSelecionado === 6 && passoExpandido !== 6}
              onSelecionar={() => selecionarEtapa(6)}
              onEditar={() => editarEtapa(6)} onFechar={fecharEtapa}
            >
              <GeradorOrcamento
                key={projetoKey}
                dadosAutomaticos={itensOrcamento}
                aoRemoverEquipamento={removerEquipamentoSugerido}
                aoReiniciar={novoProjeto}
                projetoAtual={projetoAtual}
              />
            </EtapaCard>

          </div>

        </div>
      </main>

      {/* Painel Lateral Direito */}
      <aside className="print:hidden flex flex-col min-h-0 flex-shrink-0">
        <PainelResumoLateral
          dadosGabinete={dadosDoGabinete}
          cargaCalculada={cargaCalculada}
          itensOrcamento={itensOrcamento}
          passoAtual={passoAtual}
          deltaT={deltaTCalculado}
          passoExpandido={passoSelecionado}
          itensAcessorios={itensAcessorios}
          itensTubulacao={itensTubulacao}
        />
      </aside>

      </div>{/* fim do corpo 3 colunas */}
    </div>
  );
}

function useCatalogo() {
  const [catalogo, setCatalogo] = useState(null); // null = ainda carregando
  const tentativaRef = useRef(0);

  useEffect(() => {
    let cancelado = false;

    const carregar = async () => {
      while (!cancelado) {
        try {
          const [fabricantesRes, portasRes] = await Promise.all([
            api.get('/api/v1/catalogo/paineis/fabricantes'),
            api.get('/api/v1/catalogo/portas'),
          ]);
          if (!cancelado) {
            setCatalogo({
              fabricantes: fabricantesRes.data,
              portasCatalogo: portasRes.data,
            });
          }
          return; // sucesso — encerra o loop
        } catch {
          tentativaRef.current += 1;
          if (!cancelado) await new Promise(r => setTimeout(r, 2000));
        }
      }
    };

    carregar();
    return () => { cancelado = true; };
  }, []);

  return catalogo;
}

function App() {
  const { user, loading } = useAuth();
  const catalogo = useCatalogo();

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#1a0d2e] to-[#2a1245]">
      <div className="text-white text-lg font-bold">Carregando...</div>
    </div>
  );

  if (!user) return <LoginPage />;

  if (!catalogo) return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#1a0d2e] to-[#2a1245]">
      <div className="text-center space-y-4">
        <div className="w-12 h-12 border-4 border-white/20 border-t-white rounded-full animate-spin mx-auto" />
        <p className="text-white text-lg font-bold">Conectando ao servidor...</p>
        <p className="text-purple-300 text-sm">Aguarde, isso pode levar alguns segundos</p>
      </div>
    </div>
  );

  return <AppContent catalogo={catalogo} />;
}

export default App;



