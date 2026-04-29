import React from 'react';
import PainelInsights from './PainelInsights';

const PainelResumoLateral = ({ dadosGabinete, cargaCalculada, itensOrcamento, passoAtual, cargaRealManual, deltaT }) => {
  const totalMateriais = itensOrcamento.materiais.length;
  const totalEquipamentos = itensOrcamento.equipamentos.length;

  const volumeBruto = dadosGabinete ? (dadosGabinete.comprimento * dadosGabinete.largura * dadosGabinete.altura) : 0;
  
  // Objeto de carga para os insights
  const cargaParaInsights = cargaCalculada || (cargaRealManual ? { capacidade_requerida_equipamento_kcalh: cargaRealManual } : null);

  const valorCargaExibicao = cargaParaInsights 
    ? (typeof cargaParaInsights === 'object' ? cargaParaInsights.capacidade_requerida_equipamento_kcalh : cargaParaInsights)
    : null;

  // Nova Lógica: Trocas de Ar baseada na vazão real dos evaporadores selecionados
  const evaporadores = itensOrcamento.equipamentos.filter(eq => eq.nome.toLowerCase().includes('evaporador') || eq.vazao_ar > 0);
  const vazaoTotalHoraria = evaporadores.reduce((acc, eq) => acc + (eq.vazao_ar * eq.qtde), 0);
  
  // Trocas por hora = Vazão Total / Volume da Câmara
  const trocasPorHoraBase = volumeBruto > 0 ? (vazaoTotalHoraria / volumeBruto) : 0;
  
  // Se não houver evaporadores selecionados, mostramos 0 ou um aviso
  const temEvaporador = vazaoTotalHoraria > 0;
  
  // O usuário quer o gráfico baseado na ocupação da carga (ar residual)
  // 0% Carga = Volume Total de Ar
  // 50% Carga = 50% Volume de Ar
  // 100% Carga = 10% Volume de Ar (Ar residual entre paletes)
  const trocas0 = trocasPorHoraBase;
  const trocas50 = volumeBruto > 0 ? (vazaoTotalHoraria / (volumeBruto * 0.5)) : 0;
  const trocas100 = volumeBruto > 0 ? (vazaoTotalHoraria / (volumeBruto * 0.1)) : 0;

  // Para o centro do gráfico, mostramos a média ou o valor base
  const trocasBaseExibicao = trocas0;

  return (
    <aside className="w-80 bg-white border-l border-slate-200 hidden xl:flex flex-col sticky top-0 h-screen overflow-y-auto shadow-sm">
      <div className="p-6 border-b border-purple-900/30" style={{ background: 'linear-gradient(135deg, #1a0d2e 0%, #2a1245 100%)' }}>
        <h3 className="text-sm font-black text-white uppercase tracking-widest">Resumo Técnico</h3>
        <p className="text-xs text-purple-300/70 font-bold uppercase mt-1">Indicadores em Tempo Real</p>
      </div>

      <div className="p-6 space-y-8">
        {/* INSIGHTS DE ENGENHARIA - NO TOPO */}
        {!dadosGabinete && (
          <div className="p-3 rounded-lg border-l-4 bg-white shadow-sm" style={{ borderLeftColor: '#6c5ce7' }}>
            <strong className="block text-[9px] uppercase tracking-tighter text-indigo-600">💡 Insights de Engenharia</strong>
            <p className="text-[10px] text-slate-500 leading-tight mt-1">Preencha os dados para configuração do gabinete para receber análises técnicas automaticas.</p>
          </div>
        )}
        {dadosGabinete && (
          <PainelInsights
            dimensoes={{ 
              comp: dadosGabinete.comprimento, 
              larg: dadosGabinete.largura, 
              alt: dadosGabinete.altura 
            }}
            temps={{
              interna: dadosGabinete.temperatura_interna,
              externa: 35,
              evap: deltaT != null
                ? parseFloat(dadosGabinete.temperatura_interna) - parseFloat(deltaT)
                : NaN
            }}
            isolamento={{ 
              esp: dadosGabinete.espessura, 
              nuc: dadosGabinete.nucleo 
            }}
            cargaCalculada={cargaParaInsights}
            produto={null} // Pode ser expandido se passarmos dados do produto
            compacto={true}
          />
        )}

        {/* KPI: CARGA TÉRMICA */}
        <div>
          <label className="text-xs font-black text-slate-400 uppercase tracking-widest block mb-2">Capacidade Requerida</label>
          <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-4 text-center">
            {valorCargaExibicao ? (
              <>
                <div className="text-3xl font-black text-emerald-700">
                  {valorCargaExibicao.toLocaleString()}
                </div>
                <div className="text-[10px] font-bold text-emerald-600 uppercase">kcal/h</div>
              </>
            ) : (
              <div className="text-slate-400 italic text-sm py-2">Aguardando cálculo...</div>
            )}
          </div>
        </div>

        {/* KPI: DIMENSÕES E ESTOCAGEM */}
        <div>
          <label className="text-xs font-black text-slate-400 uppercase tracking-widest block mb-2">Volume e Estocagem</label>
          {dadosGabinete ? (
            <div className="space-y-4">
              <div className="flex items-end justify-between bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div>
                   <span className="text-[11px] font-black text-slate-400 uppercase block">Volume Bruto</span>
                   <span className="text-xl font-black text-slate-800">{isNaN(volumeBruto) || volumeBruto === 0 ? '—' : volumeBruto.toFixed(1)}</span>
                   <span className="text-[10px] font-bold text-slate-400 ml-1">m³</span>
                </div>
                <div className="text-right">
                   <span className="text-[11px] font-black text-slate-400 uppercase block">Capacidade</span>
                   <span className="text-xl font-black text-blue-700">
                    {isNaN(volumeBruto) || volumeBruto === 0 ? '—' : (volumeBruto * 0.7 * 250).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
                  </span>
                  <span className="text-[10px] font-bold text-blue-400 ml-1">kg</span>
                </div>
              </div>

              {/* GRÁFICO DE TROCAS DE AR */}
              <div className="bg-white border border-slate-100 rounded-2xl p-4 shadow-sm">
                <label className="text-[11px] font-black text-slate-400 uppercase tracking-wider block mb-3">Renovação de Ar (Trocas/24h)</label>
                
                <div className="flex items-center gap-4">
                  <div className="relative w-20 h-20">
                    <svg viewBox="0 0 36 36" className="w-full h-full transform -rotate-90">
                      <circle cx="18" cy="18" r="16" fill="transparent" stroke="#f1f5f9" strokeWidth="4"></circle>
                      {/* 100% Carga (Ocupa 1/3) */}
                      <circle cx="18" cy="18" r="16" fill="transparent" stroke={temEvaporador ? "#f43f5e" : "#e2e8f0"} strokeWidth="4" strokeDasharray="33.3 100" strokeDashoffset="0"></circle>
                      {/* 50% Carga (Ocupa 1/3) */}
                      <circle cx="18" cy="18" r="16" fill="transparent" stroke={temEvaporador ? "#f59e0b" : "#e2e8f0"} strokeWidth="4" strokeDasharray="33.3 100" strokeDashoffset="-33.3"></circle>
                      {/* 0% Carga (Ocupa 1/3) */}
                      <circle cx="18" cy="18" r="16" fill="transparent" stroke={temEvaporador ? "#10b981" : "#e2e8f0"} strokeWidth="4" strokeDasharray="33.4 100" strokeDashoffset="-66.6"></circle>
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className={`text-[10px] font-black ${temEvaporador ? 'text-slate-400' : 'text-slate-300'}`}>
                        {temEvaporador ? trocasBaseExibicao.toFixed(0) : '--'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex-1 space-y-1">
                    {!temEvaporador ? (
                      <div className="text-[10px] text-slate-400 italic leading-tight">
                        Selecione um evaporador para calcular as trocas.
                      </div>
                    ) : (
                      <>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                            <span className="text-[11px] font-bold text-slate-500">Vazia</span>
                          </div>
                          <span className="text-[10px] font-black text-slate-700">{trocas0.toFixed(1)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                            <span className="text-[11px] font-bold text-slate-500">50%</span>
                          </div>
                          <span className="text-[10px] font-black text-slate-700">{trocas50.toFixed(1)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <div className="w-2 h-2 rounded-full bg-red-500"></div>
                            <span className="text-[11px] font-bold text-slate-500">100%</span>
                          </div>
                          <span className="text-[10px] font-black text-slate-700">{trocas100.toFixed(1)}</span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
                
                {/* Referências de Qualidade de Ventilação */}
                <div className="mt-4 pt-4 border-t border-slate-50">
                   <label className="text-[11px] font-black text-slate-400 uppercase tracking-wider block mb-2">Padrões de Qualidade</label>
                   <div className="space-y-2">
                      <div className="bg-slate-50 p-2 rounded-lg">
                         <div className="flex justify-between items-center mb-1">
                            <span className="text-[9px] font-bold text-slate-600">Resfriados (0°C a 5°C)</span>
                            <span className="text-[11px] font-black text-blue-600">40 a 60 trocas/h</span>
                         </div>
                         <p className="text-[8px] text-slate-400 leading-tight">Garante uniformidade de temperatura e controle de umidade.</p>
                      </div>
                      <div className="bg-slate-50 p-2 rounded-lg">
                         <div className="flex justify-between items-center mb-1">
                            <span className="text-[9px] font-bold text-slate-600">Congelados (-18°C)</span>
                            <span className="text-[11px] font-black text-blue-600">20 a 40 trocas/h</span>
                         </div>
                         <p className="text-[8px] text-slate-400 leading-tight">Foco em manter a inércia térmica e evitar bloqueio de gelo.</p>
                      </div>
                   </div>
                </div>

                <p className="text-[8px] text-slate-400 italic mt-3 leading-tight">
                  * Trocas por hora (vazão real / volume ar livre). Baseado nos evaporadores selecionados.
                </p>
              </div>
            </div>
          ) : (
            <div className="text-slate-300 italic text-sm">Não definido</div>
          )}
        </div>

        {/* LISTA DE MATERIAIS / STATUS */}
        <div>
          <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-3">Progresso do Projeto</label>
          <div className="space-y-3">
            <StatusStep label="Gabinete" completed={passoAtual > 1} active={passoAtual === 1} />
            <StatusStep label="Carga Térmica" completed={passoAtual > 2} active={passoAtual === 2} />
            <StatusStep label="Equipamentos" completed={passoAtual > 3} active={passoAtual === 3} />
            <StatusStep label="Acessórios" completed={passoAtual > 4} active={passoAtual === 4} />
            <StatusStep label="Tubulação" completed={passoAtual > 5} active={passoAtual === 5} />
          </div>
        </div>

        {/* RESUMO DO CARRINHO */}
        <div className="pt-6 border-t border-slate-100">
          <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-3">Itens no Orçamento</label>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
              <div className="text-xl font-black text-slate-700">{totalEquipamentos}</div>
              <div className="text-[10px] font-bold text-slate-400 uppercase">Máquinas</div>
            </div>
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
              <div className="text-xl font-black text-slate-700">{totalMateriais}</div>
              <div className="text-[10px] font-bold text-slate-400 uppercase">Componentes</div>
            </div>
          </div>
        </div>

        {/* DICA TÉCNICA DINÂMICA */}
        {valorCargaExibicao && (
          <div className="bg-blue-600 rounded-2xl p-5 text-white shadow-lg shadow-blue-100">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">💡</span>
              <span className="text-[10px] font-black uppercase tracking-widest">Insight de Engenharia</span>
            </div>
            <p className="text-xs leading-relaxed font-medium">
              {valorCargaExibicao > 50000 
                ? "Para cargas acima de 50.000 kcal/h, considere dividir em dois sistemas independentes para redundância."
                : "Sistema de médio porte. Verifique se o local de instalação da condensadora possui ventilação adequada."}
            </p>
          </div>
        )}
      </div>

      <div className="mt-auto p-6 bg-slate-900 text-white">
        <div className="flex justify-between items-center">
          <span className="text-[10px] font-black uppercase text-slate-400">Versão</span>
          <span className="text-[10px] font-black uppercase">1.2 PRO</span>
        </div>
      </div>
    </aside>
  );
};

const StatusStep = ({ label, completed, active }) => (
  <div className="flex items-center gap-3">
    <div className={`w-2 h-2 rounded-full ${completed ? 'bg-emerald-500' : active ? 'bg-blue-500 animate-pulse' : 'bg-slate-200'}`}></div>
    <span className={`text-xs font-bold ${completed ? 'text-slate-700' : active ? 'text-blue-600' : 'text-slate-400'}`}>{label}</span>
    {completed && <span className="text-[10px] ml-auto">✅</span>}
  </div>
);

export default PainelResumoLateral;
