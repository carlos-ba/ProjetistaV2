import React, { useState } from 'react';
import api from './api';
import { useAuth } from './contexts/AuthContext';
import LoginPage from './pages/LoginPage';

// --- IMPORTAÇÕES ---
import CalculadoraGabinete from './components/CalculadoraGabinete.jsx';
import CalculadoraCargaTermica from './components/CalculadoraCargaTermica.jsx';
import SelecaoEquipamentos from './components/SelecaoEquipamentos.jsx';
import ComponentesFluxo from './components/ComponentesFluxo.jsx';
import CalculadoraTubulacao from './components/CalculadoraTubulacao.jsx';
import GeradorOrcamento from './components/GeradorOrcamento.jsx';
import PainelResumoLateral from './components/PainelResumoLateral.jsx';


function AppContent() {
  const { user, logout } = useAuth();
  const [dadosDoGabinete, setDadosDoGabinete] = useState(null);
  const [gabineteCalculado, setGabineteCalculado] = useState(false);
  const [deltaTCalculado, setDeltaTCalculado] = useState(null);
  const [cargaCalculada, setCargaCalculada] = useState(null);
  const [itensOrcamento, setItensOrcamento] = useState({ materiais: [], equipamentos: [] });
  const [passoAtual, setPassoAtual] = useState(1);
  const [salvando, setSalvando] = useState(false);
  const [projetoAtual, setProjetoAtual] = useState(null); // { id, nome, cliente } ou null se novo
  const [listaProjetos, setListaProjetos] = useState([]);
  const [mostrandoHistorico, setMostrandoHistorico] = useState(false);

  // --- FUNÇÕES DE INTERLIGAÇÃO (PONTES) ---
  const { useCallback } = React;

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
    if (dadosCompletos.lista_corte) {
      setGabineteCalculado(true);
      setTimeout(() => {
        document.getElementById('passo-carga')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }

    if (dadosCompletos.lista_materiais) {
      setItensOrcamento(prev => ({ 
        ...prev, 
        materiais: dadosCompletos.lista_materiais,
        imagem_projeto: dadosCompletos.imagem_projeto
      }));
    } else if (dadosCompletos.imagem_projeto) {
      setItensOrcamento(prev => ({ 
        ...prev, 
        imagem_projeto: dadosCompletos.imagem_projeto
      }));
    }
    
    // Apenas muda o passo e rola se for a primeira vez ou se as dimensões mudarem significativamente
    setPassoAtual(prev => {
      if (prev < 2) {
        setTimeout(() => { document.getElementById('passo-carga')?.scrollIntoView({ behavior: 'smooth' }); }, 100);
        return 2;
      }
      return prev;
    });
  }, []);

  // 2. Recebe da Carga Térmica (Módulo 2)
  const receberResultadoCarga = useCallback((valorKcal) => {
    console.log("Carga calculada:", valorKcal);
    setCargaCalculada(valorKcal);
    setPassoAtual(prev => {
      if (prev < 3) {
        setTimeout(() => { document.getElementById('passo-selecao')?.scrollIntoView({ behavior: 'smooth' }); }, 100);
        return 3;
      }
      return prev;
    });
  }, []);
  
  // 3. Recebe da Seleção de Equipamentos (Módulo 3) - ACUMULATIVO
  const receberEquipamentosFinalizados = useCallback((equipamentos) => {
    console.log("FINALIZANDO SELEÇÃO - Lote de equipamentos recebido no App:", equipamentos);
    
    setItensOrcamento(prev => ({
      ...prev,
      equipamentos: [...prev.equipamentos, ...equipamentos]
    }));
    
    setPassoAtual(prev => {
      if (prev < 4) {
        setTimeout(() => { document.getElementById('passo-acessorios')?.scrollIntoView({ behavior: 'smooth' }); }, 100);
        return 4;
      }
      return prev;
    });
  }, []);

  // 4. Recebe dos Componentes de Fluxo (Módulo 4)
  const receberComponentesFluxo = useCallback((listaAcessorios) => {
    console.log("Acessórios selecionados:", listaAcessorios);
    setItensOrcamento(prev => ({
      ...prev,
      materiais: [...prev.materiais, ...listaAcessorios]
    }));
    setPassoAtual(prev => {
      if (prev < 5) {
        setTimeout(() => { document.getElementById('passo-tubulacao')?.scrollIntoView({ behavior: 'smooth' }); }, 100);
        return 5;
      }
      return prev;
    });
  }, []);

  // 5. Recebe da Tubulação (Módulo 5)
  const receberDadosTubulacao = useCallback((listaTubos) => {
    console.log("Tubulação calculada:", listaTubos);
    // Adiciona os tubos na lista de materiais
    setItensOrcamento(prev => ({
      ...prev,
      materiais: [...prev.materiais, ...listaTubos]
    }));
    setPassoAtual(prev => {
      if (prev < 6) {
        setTimeout(() => { document.getElementById('passo-orcamento')?.scrollIntoView({ behavior: 'smooth' }); }, 100);
        return 6;
      }
      return prev;
    });
  }, []);

  const getUltimoEquipamento = () => {
    const lista = itensOrcamento.equipamentos;
    if (lista.length === 0) return null;
    
    // Se temos vários, pegamos o último mas calculamos a capacidade real acumulada dele
    const ultimo = { ...lista[lista.length - 1] };
    if (ultimo.qtde > 1) {
      ultimo.capacidade_original = ultimo.capacidade_real;
      // Nota: Para dimensionamento de tubulação, o sistema costuma olhar o diâmetro de UMA unidade.
      // Se forem 2 unidades separadas, o tubo é para uma unidade.
      // Vou manter a capacidade individual para tubulação/acessórios, assumindo que cada unidade tem seu kit.
    }
    return ultimo;
  };

  const removerEquipamentoSugerido = (indexParaRemover) => {
    setItensOrcamento(prev => ({
      ...prev,
      equipamentos: prev.equipamentos.filter((_, index) => index !== indexParaRemover)
    }));
  };

  const novoProjeto = () => {
    if (!window.confirm("Iniciar novo projeto? Os dados não salvos serão perdidos.")) return;
    setDadosDoGabinete(null);
    setCargaCalculada(null);
    setItensOrcamento({ materiais: [], equipamentos: [] });
    setPassoAtual(1);
    setProjetoAtual(null);
    setGabineteCalculado(false);
    setDeltaTCalculado(null);
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
        const resp = await api.post('/api/v1/projetos/', _montarPayload(nome));
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
      await api.put(`/api/v1/projetos/${projetoAtual.id}/`, _montarPayload(projetoAtual.nome, projetoAtual.cliente));
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
      const resp = await api.post('/api/v1/projetos/', _montarPayload(nome, projetoAtual?.cliente));
      setProjetoAtual({ id: resp.data.id, nome: resp.data.nome, cliente: resp.data.cliente });
      alert(`Projeto salvo como "${nome}"!`);
      if (mostrandoHistorico) abrirHistorico();
    } catch { alert("Erro ao salvar o projeto."); }
    finally { setSalvando(false); }
  };

  const abrirHistorico = async () => {
    try {
      const resp = await api.get('/api/v1/projetos/');
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
    <div className="min-h-screen bg-slate-50 flex print:bg-white">
      {/* Sidebar Lateral Moderna */}
      <aside className="w-64 text-white flex-shrink-0 hidden lg:flex flex-col print:hidden" style={{ background: 'linear-gradient(180deg, #1a0d2e 0%, #2a1245 100%)' }}>
        <div className="p-6">
          <img
            src="/static/logoIceNexusIAR.png"
            alt="IceNexus IAR"
            className="w-full max-h-20 object-contain mb-4"
          />
          <h1 className="text-2xl font-black bg-gradient-to-r from-green-400 to-purple-400 bg-clip-text text-transparent">
            PROJETISTA 360
          </h1>
          <p className="text-purple-300/60 text-xs mt-1 font-medium uppercase tracking-widest">Engineering Suite</p>
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-4">
          <div className="p-3 rounded-lg flex items-center gap-3 cursor-pointer" style={{ background: 'rgba(123,45,139,0.5)' }}>
            <span>📐</span> <span className="font-semibold">Projeto Atual</span>
          </div>
          <div
            onClick={abrirHistorico}
            className="p-3 rounded-lg flex items-center gap-3 cursor-pointer transition-colors text-purple-200/70 hover:text-white"
            style={{ '--tw-bg-opacity': 1 }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(123,45,139,0.25)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <span>📁</span> <span>Histórico</span>
          </div>
          <div
            className="p-3 rounded-lg flex items-center gap-3 cursor-pointer transition-colors text-purple-200/70 hover:text-white"
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(123,45,139,0.25)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <span>⚙️</span> <span>Configurações</span>
          </div>
        </nav>

        <div className="p-4 border-t border-purple-900/50">
          <div className="p-4 rounded-xl" style={{ background: 'rgba(107,191,63,0.1)', border: '1px solid rgba(107,191,63,0.2)' }}>
            <p className="text-xs text-slate-400">Status do Servidor</p>
            <div className="flex items-center gap-2 mt-1">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-bold text-emerald-500">Conectado</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Área de Conteúdo Principal */}
      <main className="flex-1 flex flex-col h-screen overflow-y-auto print:h-auto print:overflow-visible print:bg-white">
        <header className="bg-white border-b border-slate-200 sticky top-0 z-20 shadow-sm print:hidden">
          <div className="p-4 flex justify-between items-center">
            <div>
              <h2 className="text-slate-800 font-bold text-lg">
                {projetoAtual ? projetoAtual.nome : 'Novo Dimensionamento Frigorífico'}
              </h2>
              {projetoAtual ? (
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Projeto #{projetoAtual.id}</p>
              ) : (
                <span className="text-[10px] font-bold bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full uppercase tracking-wide">Projeto não salvo</span>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={novoProjeto}
                className="text-slate-500 px-3 py-2 rounded-lg text-sm font-bold hover:bg-slate-100 transition-colors"
              >
                + Novo
              </button>
              <button
                onClick={salvarComo}
                disabled={salvando}
                className="border-2 border-[#7B2D8B] text-[#7B2D8B] px-3 py-2 rounded-lg text-sm font-bold hover:bg-purple-50 transition-colors disabled:opacity-50"
              >
                Salvar Como
              </button>
              <button
                onClick={salvarProjeto}
                disabled={salvando}
                className={`bg-[#7B2D8B] text-white px-4 py-2 rounded-lg text-sm font-bold transition-colors ${salvando ? 'opacity-50 cursor-not-allowed' : 'hover:bg-purple-800'}`}
              >
                {salvando ? 'Salvando...' : 'Salvar Projeto'}
              </button>
              <div className="flex items-center gap-2 ml-2 pl-2 border-l border-slate-200">
                <span className="text-xs text-slate-500 font-medium hidden sm:block">{user.username}</span>
                <button
                  onClick={logout}
                  className="text-slate-400 hover:text-red-500 px-2 py-2 rounded-lg text-sm transition-colors"
                  title="Sair"
                >
                  ⏏
                </button>
              </div>
            </div>
          </div>
          
          {/* Progress Tracker Visual - Agora dentro do header fixo */}
          <div className="px-8 pb-6 max-w-4xl mx-auto w-full">
            <div className="flex justify-between items-center relative">
              <div className="absolute h-1 bg-slate-200 left-0 right-0 top-1/2 -translate-y-1/2 z-0"></div>
              {[1, 2, 3, 4, 5, 6].map(step => (
                <div key={step} className="flex flex-col items-center z-10">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold border-4 transition-all duration-500 ${
                    step === passoAtual
                      ? 'bg-[#7B2D8B] text-white border-purple-200 scale-110 shadow-lg shadow-purple-200'
                      : step < passoAtual
                        ? 'bg-[#6BBF3F] text-white border-green-100'
                        : 'bg-white text-slate-400 border-slate-200'
                  }`}>
                    {step < passoAtual ? '✓' : step}
                  </div>
                  <span className={`text-[10px] font-bold uppercase mt-1 absolute -bottom-5 whitespace-nowrap ${
                    step === passoAtual ? 'text-[#7B2D8B]' : 'text-slate-400'
                  }`}>
                    {step === 1 && 'Gabinete'}
                    {step === 2 && 'Carga'}
                    {step === 3 && 'Equipamento'}
                    {step === 4 && 'Acessórios'}
                    {step === 5 && 'Tubulação'}
                    {step === 6 && 'Orçamento'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </header>

        <div className="p-8 pt-12 max-w-5xl mx-auto w-full space-y-12 print:p-0 print:max-w-none print:m-0">
          
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

          <section id="v2-gabinete" className="scroll-mt-40 print:hidden">
            <CalculadoraGabinete aoFinalizar={receberDadosGabinete} />
          </section>

          {/* Módulos seguintes aparecem conforme o usuário avança no projeto */}
          
          {gabineteCalculado && (
            <section id="passo-carga" className="animate-in fade-in duration-700 scroll-mt-40 print:hidden">
               <CalculadoraCargaTermica dadosIniciais={dadosDoGabinete} aoFinalizar={receberResultadoCarga} />
            </section>
          )}

          {cargaCalculada && (
            <section id="passo-selecao" className="animate-in fade-in duration-700 scroll-mt-40 print:hidden">
              <SelecaoEquipamentos
                cargaInicial={cargaCalculada}
                tempInterna={dadosDoGabinete?.temperatura_interna}
                onDeltaTChange={setDeltaTCalculado}
                aoFinalizar={receberEquipamentosFinalizados}
              />
            </section>
          )}

          {itensOrcamento.equipamentos.length > 0 && (
            <section id="passo-acessorios" className="animate-in fade-in duration-700 scroll-mt-40 print:hidden">
               <ComponentesFluxo 
                 cargaAlvo={getUltimoEquipamento()?.capacidade_real || cargaCalculada} 
                 fluido={getUltimoEquipamento()?.fluido || 'R404A'}
                 tempEvap={getUltimoEquipamento()?.temp_evap || -10}
                 aoFinalizar={receberComponentesFluxo} 
               />
            </section>
          )}

          {passoAtual >= 5 && (
            <section id="passo-tubulacao" className="animate-in fade-in duration-700 scroll-mt-40 print:hidden">
              <CalculadoraTubulacao equipamentoSelecionado={getUltimoEquipamento()} aoFinalizar={receberDadosTubulacao} />
            </section>
          )}

          {/* O orçamento aparece se houver qualquer item (materiais ou equipamentos) */}
          {(itensOrcamento.materiais.length > 0 || itensOrcamento.equipamentos.length > 0) && (
            <section id="passo-orcamento" className="animate-in fade-in duration-700 scroll-mt-40">
              <GeradorOrcamento 
                dadosAutomaticos={itensOrcamento} 
                aoRemoverEquipamento={removerEquipamentoSugerido} 
                aoReiniciar={novoProjeto}
              />
            </section>
          )}

          {!dadosDoGabinete && (
            <div className="p-12 bg-white rounded-2xl border-2 border-dashed border-slate-200 flex flex-col items-center justify-center text-center print:hidden">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center text-2xl mb-4">🧊</div>
              <h3 className="text-slate-800 font-bold text-lg">Aguardando Início do Projeto</h3>
              <p className="text-slate-500 max-w-xs mt-2">
                Preencha os dados do gabinete acima e clique em calcular para desbloquear os próximos passos da engenharia.
              </p>
            </div>
          )}

        </div>
      </main>

      {/* PAINEL RESUMO LATERAL (Ocupa o espaço em branco na direita) */}
      <aside className="print:hidden">
        <PainelResumoLateral
          dadosGabinete={dadosDoGabinete}
          cargaCalculada={cargaCalculada}
          itensOrcamento={itensOrcamento}
          passoAtual={passoAtual}
          deltaT={deltaTCalculado}
        />
      </aside>
    </div>
  );
}

function App() {
  const { user, loading } = useAuth();

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#1a0d2e] to-[#2a1245]">
      <div className="text-white text-lg font-bold">Carregando...</div>
    </div>
  );

  if (!user) return <LoginPage />;

  return <AppContent />;
}

export default App;
