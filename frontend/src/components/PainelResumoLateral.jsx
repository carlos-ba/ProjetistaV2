import React, { useState, useEffect } from 'react';
import api from '../api';

// ── Status da cotação (Card 6) ────────────────────────────────────────────
const ESTADOS_COTACAO = {
  sem_projeto: { bg: 'bg-slate-50 border-slate-100',     dot: 'bg-slate-400',   txt: 'Salve o projeto para cotar' },
  carregando:  { bg: 'bg-slate-50 border-slate-100',     dot: 'bg-slate-300',   txt: 'Verificando…' },
  nenhuma:     { bg: 'bg-rose-50 border-rose-100',       dot: 'bg-rose-500',    txt: 'Sem cotação — gere a planilha' },
  aguardando:  { bg: 'bg-amber-50 border-amber-100',     dot: 'bg-amber-500',   txt: 'Aguardando fornecedor' },
  processada:  { bg: 'bg-emerald-50 border-emerald-100', dot: 'bg-emerald-500', txt: 'Cotação processada — pronto p/ proposta' },
};

const StatusCotacao = ({ projetoId }) => {
  const [status, setStatus] = useState(projetoId ? 'carregando' : 'sem_projeto');
  useEffect(() => {
    if (!projetoId) { setStatus('sem_projeto'); return; }
    let cancelado = false;
    setStatus('carregando');
    api.get(`/api/v1/cotacoes?projeto_id=${projetoId}`)
      .then(r => {
        if (cancelado) return;
        const cot = (r.data || []).filter(c => c.status !== 'cancelada');
        const proc = cot.filter(c => c.status === 'processada');
        setStatus(cot.length === 0 ? 'nenhuma' : proc.length ? 'processada' : 'aguardando');
      })
      .catch(() => { if (!cancelado) setStatus('nenhuma'); });
    return () => { cancelado = true; };
  }, [projetoId]);

  const e = ESTADOS_COTACAO[status];
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${e.bg}`}>
      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${e.dot}`} />
      <div>
        <p className="text-[9px] font-black uppercase tracking-wide text-slate-400">Status da cotação</p>
        <p className="text-[11px] font-bold text-slate-700 leading-tight">{e.txt}</p>
      </div>
    </div>
  );
};

// ── Detalhe rico por etapa ────────────────────────────────────────────────
const DetalheEtapa = ({ passoExpandido, dadosGabinete, cargaCalculada, itensOrcamento, deltaT, tempExterna, itensAcessorios, itensTubulacao, projetoAtual }) => {

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
    // Estimativa antes da seleção de equipamento (Card 3) — mesma conta usada
    // no Painel Técnico da sidebar esquerda: T.Evap = T.Interna − Delta T.
    // T.Cond segue a regra do projeto: T.Amb + 10°C.
    const tEvapEstimado = (deltaT != null && dadosGabinete?.temperatura_interna != null)
      ? (Number(dadosGabinete.temperatura_interna) - Number(deltaT)).toFixed(1)
      : null;
    const tCondEstimado = tempExterna != null ? (Number(tempExterna) + 10).toFixed(1) : null;
    return (
      <div className="space-y-3">
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center">
          <p className="text-[10px] font-black text-emerald-600 uppercase tracking-widest">Capacidade Requerida</p>
          <p className="text-3xl font-black text-emerald-700 mt-1">{carga.toLocaleString('pt-BR')}</p>
          <p className="text-xs text-emerald-500 font-bold">kcal/h</p>
        </div>
        {(tEvapEstimado != null || tCondEstimado != null) && (
          <div className="flex gap-2">
            {tEvapEstimado != null && (
              <div className="flex-1 bg-slate-50 border border-slate-100 rounded-lg p-2 text-center">
                <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">T.Evap (est.)</p>
                <p className="text-sm font-bold text-slate-700">{tEvapEstimado}°C</p>
              </div>
            )}
            {tCondEstimado != null && (
              <div className="flex-1 bg-slate-50 border border-slate-100 rounded-lg p-2 text-center">
                <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">T.Cond (est.)</p>
                <p className="text-sm font-bold text-slate-700">{tCondEstimado}°C</p>
              </div>
            )}
          </div>
        )}
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

    // Capacidade nominal = média aritmética das capacidades individuais (unidades × qtde)
    const totalQtde  = equips.reduce((s, e) => s + e.qtde, 0);
    const somaCapAll = equips.reduce((s, e) => s + (e.capacidade_real * e.qtde), 0);
    const capNominal = totalQtde > 0 ? Math.round(somaCapAll / totalQtde) : 0;

    // Parâmetros de seleção (pega do primeiro equipamento — todos usam o mesmo critério)
    const ref       = equips[0];
    const tEvap     = ref?.temp_evap   ?? '—';
    const tCond     = ref?.temp_cond   ?? '—';
    const deltaTEq  = (tEvap !== '—' && deltaT != null) ? deltaT : null;

    return (
      <div className="space-y-2">
        {/* Cards dos equipamentos */}
        {equips.map((e, i) => (
          <div key={i} className="bg-slate-50 rounded-lg p-3 border border-slate-100">
            <p className="text-xs font-bold text-slate-700 truncate">{e.nome}</p>
            <div className="flex justify-between mt-1">
              <span className="text-[10px] text-slate-500">{e.qtde}× {e.capacidade_real.toLocaleString('pt-BR')} kcal/h</span>
              <span className="text-[10px] font-bold text-blue-600">{e.fluido}</span>
            </div>
          </div>
        ))}

        {/* Capacidade nominal (média) */}
        <div className="pt-2 border-t border-slate-100 space-y-2">
          <Chip label="Capacidade nominal" valor={`${capNominal.toLocaleString('pt-BR')} kcal/h`} destaque />
        </div>

        {/* Parâmetros de seleção */}
        <div className="pt-1 space-y-1.5">
          <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Parâmetros de Seleção</p>
          <Chip label="T. Evaporação" valor={tEvap !== '—' ? `${tEvap}°C` : '—'} />
          <Chip label="T. Condensação" valor={tCond !== '—' ? `${tCond}°C` : '—'} />
          {deltaTEq != null && (
            <Chip label="Delta T evaporador" valor={`${deltaTEq}°C`} />
          )}
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
    return (
      <div className="space-y-3">
        <StatusCotacao projetoId={projetoAtual?.id} />
        <Chip label="Materiais" valor={`${itensOrcamento.materiais.length}`} />
        <Chip label="Equipamentos" valor={`${itensOrcamento.equipamentos.length}`} />
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
  passoAtual, deltaT, tempExterna, passoExpandido,
  itensAcessorios, itensTubulacao, projetoAtual,
  inputsEquipamentos,
}) => {
  const volumeBruto      = dadosGabinete
    ? dadosGabinete.comprimento * dadosGabinete.largura * dadosGabinete.altura
    : 0;

  const valorCarga = cargaCalculada ? Number(cargaCalculada) : null;
  const etapaAtual = ETAPAS[passoExpandido];

  // Regime de seleção — parâmetros usados para buscar os equipamentos (Etapa 3)
  const regimeEvap   = inputsEquipamentos?.evap   !== '' && inputsEquipamentos?.evap   != null && !isNaN(inputsEquipamentos.evap)   ? Number(inputsEquipamentos.evap)   : null;
  const regimeCond   = inputsEquipamentos?.cond   !== '' && inputsEquipamentos?.cond   != null && !isNaN(inputsEquipamentos.cond)   ? Number(inputsEquipamentos.cond)   : null;
  const regimeFluido = inputsEquipamentos?.fluido || null;

  // Trocas de ar
  const evaporadores      = itensOrcamento.equipamentos.filter(e => e.vazao_ar > 0);
  const vazaoTotalHoraria = evaporadores.reduce((a, e) => a + e.vazao_ar * e.qtde, 0);
  const trocas0     = volumeBruto > 0 ? vazaoTotalHoraria / volumeBruto : 0;          // câmara vazia — base da norma (FAO)
  const trocasMeia  = volumeBruto > 0 ? vazaoTotalHoraria / (volumeBruto * 0.5) : 0;  // ~50% ocupada (informativo)
  const trocasCheia = volumeBruto > 0 ? vazaoTotalHoraria / (volumeBruto * 0.1) : 0;  // cheia, ~10% de ar livre (informativo)
  const temEvap     = vazaoTotalHoraria > 0;

  // Faixa recomendada de trocas/h por aplicação (FAO/ASHRAE), sobre o volume vazio.
  const tempInt     = dadosGabinete?.temperatura_interna != null ? Number(dadosGabinete.temperatura_interna) : null;
  const ehCongelados = tempInt != null && tempInt < -5;
  const faixaRec    = ehCongelados ? [40, 60] : [20, 30];
  const aplicacao   = ehCongelados ? 'Congelados' : 'Resfriados';
  let veredito = null;
  if (temEvap) {
    if (trocas0 < faixaRec[0])
      veredito = { cor: 'amber', txt: 'Abaixo do recomendado — risco de zonas mortas / má distribuição de ar.' };
    else if (trocas0 > faixaRec[1])
      veredito = { cor: 'rose', txt: 'Acima do recomendado — risco de ressecamento em produto não embalado; avaliar evaporador de menor vazão.' };
    else
      veredito = { cor: 'emerald', txt: 'Circulação dentro da faixa recomendada.' };
  }
  const CORES = {
    amber:   { txt: 'text-amber-600',   bg: 'bg-amber-50',   ring: 'text-amber-500' },
    rose:    { txt: 'text-rose-600',    bg: 'bg-rose-50',    ring: 'text-rose-500' },
    emerald: { txt: 'text-emerald-600', bg: 'bg-emerald-50', ring: 'text-emerald-500' },
  };

  return (
    <aside className="w-80 bg-white border-l border-slate-200 hidden xl:flex flex-col overflow-y-auto shadow-sm" style={{ height: '100%', maxHeight: '100vh' }}>


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
            tempExterna={tempExterna}
            itensAcessorios={itensAcessorios}
            itensTubulacao={itensTubulacao}
            projetoAtual={projetoAtual}
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

          {/* Regime de seleção — só aparece depois de calculada a carga térmica */}
          {valorCarga != null && (
            <div className="mt-2 grid grid-cols-3 gap-2">
              <div className="bg-slate-50 border border-slate-100 rounded-lg p-2 text-center">
                <span className="text-[9px] font-black text-slate-400 uppercase block">T. Evap</span>
                <span className="text-sm font-bold text-slate-700">{regimeEvap != null ? `${regimeEvap}°C` : '—'}</span>
              </div>
              <div className="bg-slate-50 border border-slate-100 rounded-lg p-2 text-center">
                <span className="text-[9px] font-black text-slate-400 uppercase block">T. Cond</span>
                <span className="text-sm font-bold text-slate-700">{regimeCond != null ? `${regimeCond}°C` : '—'}</span>
              </div>
              <div className="bg-slate-50 border border-slate-100 rounded-lg p-2 text-center">
                <span className="text-[9px] font-black text-slate-400 uppercase block">Fluido</span>
                <span className="text-sm font-bold text-blue-600">{regimeFluido || '—'}</span>
              </div>
            </div>
          )}
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

              {/* Renovação de ar (recirculação do evaporador) */}
              <div className="bg-white border border-slate-100 rounded-2xl p-4 shadow-sm">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-3">
                  Renovação de Ar (trocas/h)
                </label>
                {!temEvap ? (
                  <p className="text-[10px] text-slate-400 italic">Selecione um evaporador para calcular.</p>
                ) : (
                  <>
                    {/* Indicador principal — câmara vazia (base da norma) */}
                    <div className="flex items-end gap-2">
                      <span className={`text-3xl font-black ${veredito ? CORES[veredito.cor].txt : 'text-slate-800'}`}>
                        {trocas0.toFixed(0)}
                      </span>
                      <span className="text-[10px] text-slate-400 mb-1.5">trocas/h · câmara vazia</span>
                    </div>

                    {/* Faixa recomendada + veredito */}
                    <div className={`mt-2 rounded-lg px-3 py-2 ${veredito ? CORES[veredito.cor].bg : 'bg-slate-50'}`}>
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="font-bold text-slate-500">Recomendado ({aplicacao})</span>
                        <span className="font-black text-slate-700">{faixaRec[0]}–{faixaRec[1]}/h</span>
                      </div>
                      {veredito && (
                        <p className={`text-[10px] mt-1 leading-snug ${CORES[veredito.cor].txt}`}>{veredito.txt}</p>
                      )}
                    </div>

                    {/* Secundário — informativo, com a câmara carregada (não comparar com a norma) */}
                    <div className="mt-2 pt-2 border-t border-slate-100">
                      <p className="text-[9px] text-slate-400 uppercase font-bold mb-1">Recirculação sobre o ar livre com a câmara carregada (informativo)</p>
                      <div className="flex items-center justify-between text-[10px] text-slate-500">
                        <span>Meia carga: <b className="text-slate-600">{trocasMeia.toFixed(0)}</b>/h</span>
                        <span>Cheia (~10% livre): <b className="text-slate-600">{trocasCheia.toFixed(0)}</b>/h</span>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

      </div>

    </aside>
  );
};

export default PainelResumoLateral;
