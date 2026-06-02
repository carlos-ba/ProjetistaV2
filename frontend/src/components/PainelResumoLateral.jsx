import React from 'react';

// ── Detalhe rico por etapa ────────────────────────────────────────────────
const DetalheEtapa = ({ passoExpandido, dadosGabinete, cargaCalculada, itensOrcamento, deltaT, itensAcessorios, itensTubulacao }) => {

  if (!passoExpandido) return (
    <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-center">
      <p className="text-xs text-slate-400 italic">Selecione uma etapa para ver o detalhamento.</p>
    </div>
  );

  // ── Etapa 1: Gabinete ──
  if (passoExpandido === 1) {
    const g = dadosGabinete;
    if (!g) return <p className="text-xs text-slate-400 italic">Preencha os dados do gabinete.</p>;
    const volume = (g.comprimento * g.largura * g.altura).toFixed(1);
    const capKg  = (g.comprimento * g.largura * g.altura * 0.7 * 250).toLocaleString('pt-BR', { maximumFractionDigits: 0 });
    return (
      <div className="space-y-3">
        <Chip label="Dimensões" valor={`${g.comprimento} × ${g.largura} × ${g.altura} m`} />
        <Chip label="Volume" valor={`${volume} m³`} />
        <Chip label="Temperatura interna" valor={`${g.temperatura_interna}°C`} destaque />
        <Chip label="Isolamento" valor={`${g.nucleo} — ${g.espessura} mm`} />
        <Chip label="Tipo de piso" valor={g.tipo_piso === 'painel' ? 'Painel frigorífico' : g.tipo_piso === 'convencional' ? 'Isolado (concreto)' : 'Sem isolamento'} />
        <Chip label="Cap. estocagem estimada" valor={`${capKg} kg`} />
        {g.u_global && <Chip label="U Global do painel" valor={`${g.u_global} W/(m²·K)`} destaque />}
      </div>
    );
  }

  // ── Etapa 2: Carga Térmica ──
  if (passoExpandido === 2) {
    if (!cargaCalculada) return <p className="text-xs text-slate-400 italic">Execute o cálculo de carga térmica.</p>;
    const carga = Number(cargaCalculada);
    const tr = (carga / 3024).toFixed(2);
    const kw = (carga / 860).toFixed(2);
    return (
      <div className="space-y-3">
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center">
          <p className="text-[10px] font-black text-emerald-600 uppercase tracking-widest">Capacidade Requerida</p>
          <p className="text-3xl font-black text-emerald-700 mt-1">{carga.toLocaleString('pt-BR')}</p>
          <p className="text-xs text-emerald-500 font-bold">kcal/h</p>
        </div>
        <Chip label="Equivalente em TR" valor={`${tr} TR`} />
        <Chip label="Equivalente em kW" valor={`${kw} kW`} />
        {deltaT && <Chip label="Delta T selecionado" valor={`${deltaT}°C`} destaque />}
      </div>
    );
  }

  // ── Etapa 3: Equipamentos ──
  if (passoExpandido === 3) {
    const equips = itensOrcamento.equipamentos;
    if (equips.length === 0) return <p className="text-xs text-slate-400 italic">Nenhum equipamento selecionado ainda.</p>;
    const totalCap = equips.reduce((s, e) => s + (e.capacidade_real * e.qtde), 0);
    return (
      <div className="space-y-2">
        {equips.map((e, i) => (
          <div key={i} className="bg-slate-50 rounded-lg p-3 border border-slate-100">
            <p className="text-xs font-bold text-slate-700 truncate">{e.nome}</p>
            <div className="flex justify-between mt-1">
              <span className="text-[10px] text-slate-500">{e.qtde}× {e.capacidade_real} kcal/h</span>
              <span className="text-[10px] font-bold text-blue-600">{e.fluido}</span>
            </div>
          </div>
        ))}
        <div className="pt-2 border-t border-slate-100">
          <Chip label="Capacidade total" valor={`${totalCap.toLocaleString('pt-BR')} kcal/h`} destaque />
        </div>
      </div>
    );
  }

  // ── Etapa 4: Acessórios ──
  if (passoExpandido === 4) {
    if (!itensAcessorios || itensAcessorios.length === 0)
      return <p className="text-xs text-slate-400 italic">Confirme os acessórios de fluxo.</p>;
    return (
      <div className="space-y-2">
        {itensAcessorios.map((m, i) => (
          <div key={i} className="bg-slate-50 rounded-lg px-3 py-2 border border-slate-100">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#7B2D8B] flex-shrink-0"/>
              <span className="text-xs font-bold text-slate-700 truncate">{m.item}</span>
            </div>
            {m.detalhe && (
              <p className="text-[10px] text-slate-400 mt-0.5 pl-3.5 truncate">{m.detalhe}</p>
            )}
          </div>
        ))}
      </div>
    );
  }

  // ── Etapa 5: Tubulação ──
  if (passoExpandido === 5) {
    if (!itensTubulacao || itensTubulacao.length === 0)
      return <p className="text-xs text-slate-400 italic">Execute o dimensionamento de tubulação.</p>;
    return (
      <div className="space-y-2">
        {itensTubulacao.map((t, i) => (
          <div key={i} className="flex items-start gap-2 bg-slate-50 rounded-lg px-3 py-2 border border-slate-100">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 flex-shrink-0 mt-1"/>
            <div>
              <span className="text-xs font-bold text-slate-700 block">{t.item || t.descricao}</span>
              {(t.quantidade || t.comprimento) && (
                <span className="text-[10px] text-slate-400">
                  {t.quantidade && `Qtd: ${t.quantidade}`}
                  {t.comprimento && ` | ${t.comprimento}m`}
                  {t.area_total && ` | ${t.area_total}m²`}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // ── Etapa 6: Orçamento ──
  if (passoExpandido === 6) {
    const totalEq = itensOrcamento.equipamentos.reduce((s, e) => s + (e.preco * e.qtde), 0);
    return (
      <div className="space-y-3">
        <Chip label="Equipamentos" valor={`R$ ${totalEq.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`} />
        <Chip label="Total de itens" valor={`${itensOrcamento.equipamentos.length + itensOrcamento.materiais.length} itens`} destaque />
      </div>
    );
  }

  return null;
};

const Chip = ({ label, valor, destaque }) => (
  <div className={`flex justify-between items-center px-3 py-2 rounded-lg ${destaque ? 'bg-purple-50 border border-purple-100' : 'bg-slate-50 border border-slate-100'}`}>
    <span className={`text-[10px] font-bold uppercase tracking-wide ${destaque ? 'text-purple-600' : 'text-slate-500'}`}>{label}</span>
    <span className={`text-xs font-black ${destaque ? 'text-purple-800' : 'text-slate-700'}`}>{valor}</span>
  </div>
);

// ── Labels das etapas ─────────────────────────────────────────────────────
const ETAPAS = {
  1: { icone: '📏', label: 'Configuração do Gabinete' },
  2: { icone: '❄️', label: 'Cálculo de Carga Térmica' },
  3: { icone: '⚙️', label: 'Seleção de Equipamentos' },
  4: { icone: '🔧', label: 'Componentes e Acessórios' },
  5: { icone: '🔩', label: 'Dimensionamento de Tubulação' },
  6: { icone: '💰', label: 'Gerador de Orçamento' },
};

// ── Componente principal ──────────────────────────────────────────────────
const PainelResumoLateral = ({
  dadosGabinete, cargaCalculada, itensOrcamento,
  passoAtual, deltaT, passoExpandido,
  itensAcessorios, itensTubulacao,
}) => {
  const totalMateriais   = itensOrcamento.materiais.length;
  const totalEquipamentos= itensOrcamento.equipamentos.length;
  const volumeBruto      = dadosGabinete
    ? dadosGabinete.comprimento * dadosGabinete.largura * dadosGabinete.altura
    : 0;

  const valorCarga = cargaCalculada ? Number(cargaCalculada) : null;
  const etapaAtual = ETAPAS[passoExpandido];

  // Trocas de ar
  const evaporadores      = itensOrcamento.equipamentos.filter(e => e.vazao_ar > 0);
  const vazaoTotalHoraria = evaporadores.reduce((a, e) => a + e.vazao_ar * e.qtde, 0);
  const trocas0   = volumeBruto > 0 ? vazaoTotalHoraria / volumeBruto : 0;
  const trocas50  = volumeBruto > 0 ? vazaoTotalHoraria / (volumeBruto * 0.5) : 0;
  const trocas100 = volumeBruto > 0 ? vazaoTotalHoraria / (volumeBruto * 0.1) : 0;
  const temEvap   = vazaoTotalHoraria > 0;

  return (
    <aside className="w-80 bg-white border-l border-slate-200 hidden xl:flex flex-col sticky top-0 h-screen overflow-y-auto shadow-sm">

      {/* Cabeçalho */}
      <div className="p-5 border-b border-purple-900/30 flex-shrink-0"
           style={{ background: 'linear-gradient(135deg, #1a0d2e 0%, #2a1245 100%)' }}>
        <h3 className="text-sm font-black text-white uppercase tracking-widest">Painel Técnico</h3>
        <p className="text-xs text-purple-300/70 font-bold uppercase mt-0.5">Indicadores em tempo real</p>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-6">

        {/* ── DETALHE DA ETAPA ATIVA ── */}
        <div className="rounded-xl border-2 border-[#7B2D8B]/30 bg-purple-50/40 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[#7B2D8B]/20">
            <span className="w-1.5 h-1.5 rounded-full bg-[#7B2D8B] animate-pulse flex-shrink-0"/>
            <span className="text-[10px] font-black text-[#7B2D8B] uppercase tracking-widest">
              {etapaAtual ? `${etapaAtual.icone} ${etapaAtual.label}` : '📋 Detalhes da Etapa'}
            </span>
          </div>
          <DetalheEtapa
            passoExpandido={passoExpandido}
            dadosGabinete={dadosGabinete}
            cargaCalculada={cargaCalculada}
            itensOrcamento={itensOrcamento}
            deltaT={deltaT}
            itensAcessorios={itensAcessorios}
            itensTubulacao={itensTubulacao}
          />
        </div>

        {/* ── KPI: CAPACIDADE REQUERIDA ── */}
        <div>
          <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">
            Capacidade Requerida
          </label>
          <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-4 text-center">
            {valorCarga ? (
              <>
                <div className="text-3xl font-black text-emerald-700">{valorCarga.toLocaleString('pt-BR')}</div>
                <div className="text-[10px] font-bold text-emerald-600 uppercase">kcal/h</div>
              </>
            ) : (
              <div className="text-slate-400 italic text-sm py-2">Aguardando cálculo...</div>
            )}
          </div>
        </div>

        {/* ── VOLUME E TROCAS DE AR ── */}
        {dadosGabinete && (
          <div>
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">
              Volume e Ventilação
            </label>
            <div className="space-y-3">
              <div className="flex justify-between bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div>
                  <span className="text-[10px] font-black text-slate-400 uppercase block">Volume</span>
                  <span className="text-xl font-black text-slate-800">{volumeBruto.toFixed(1)}</span>
                  <span className="text-[10px] text-slate-400 ml-1">m³</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] font-black text-slate-400 uppercase block">Estocagem</span>
                  <span className="text-xl font-black text-blue-700">
                    {(volumeBruto * 0.7 * 250).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
                  </span>
                  <span className="text-[10px] text-blue-400 ml-1">kg</span>
                </div>
              </div>

              {/* Gráfico trocas de ar */}
              <div className="bg-white border border-slate-100 rounded-2xl p-4 shadow-sm">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-3">
                  Renovação de Ar (trocas/h)
                </label>
                <div className="flex items-center gap-4">
                  <div className="relative w-16 h-16 flex-shrink-0">
                    <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                      <circle cx="18" cy="18" r="16" fill="transparent" stroke="#f1f5f9" strokeWidth="4"/>
                      <circle cx="18" cy="18" r="16" fill="transparent" stroke={temEvap ? "#f43f5e" : "#e2e8f0"} strokeWidth="4" strokeDasharray="33.3 100" strokeDashoffset="0"/>
                      <circle cx="18" cy="18" r="16" fill="transparent" stroke={temEvap ? "#f59e0b" : "#e2e8f0"} strokeWidth="4" strokeDasharray="33.3 100" strokeDashoffset="-33.3"/>
                      <circle cx="18" cy="18" r="16" fill="transparent" stroke={temEvap ? "#10b981" : "#e2e8f0"} strokeWidth="4" strokeDasharray="33.4 100" strokeDashoffset="-66.6"/>
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-[9px] font-black text-slate-400">{temEvap ? trocas0.toFixed(0) : '--'}</span>
                    </div>
                  </div>
                  <div className="flex-1 space-y-1 text-[10px]">
                    {!temEvap ? (
                      <p className="text-slate-400 italic">Selecione um evaporador para calcular.</p>
                    ) : (
                      <>
                        {[['Vazia', 'bg-emerald-500', trocas0],['50%', 'bg-amber-500', trocas50],['100%', 'bg-red-500', trocas100]].map(([l,c,v]) => (
                          <div key={l} className="flex items-center justify-between">
                            <div className="flex items-center gap-1.5">
                              <div className={`w-2 h-2 rounded-full ${c}`}/>
                              <span className="font-bold text-slate-500">{l}</span>
                            </div>
                            <span className="font-black text-slate-700">{v.toFixed(1)}</span>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── ITENS NO ORÇAMENTO ── */}
        <div>
          <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">
            Itens no Orçamento
          </label>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-100 text-center">
              <div className="text-2xl font-black text-slate-700">{totalEquipamentos}</div>
              <div className="text-[10px] font-bold text-slate-400 uppercase">Máquinas</div>
            </div>
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-100 text-center">
              <div className="text-2xl font-black text-slate-700">{totalMateriais}</div>
              <div className="text-[10px] font-bold text-slate-400 uppercase">Itens</div>
            </div>
          </div>
        </div>

      </div>

      {/* Rodapé */}
      <div className="p-4 bg-slate-900 text-white flex-shrink-0">
        <div className="flex justify-between items-center">
          <span className="text-[10px] font-black uppercase text-slate-400">Versão</span>
          <span className="text-[10px] font-black uppercase">1.2 PRO</span>
        </div>
      </div>
    </aside>
  );
};

export default PainelResumoLateral;
