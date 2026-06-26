import React, { useRef, useEffect, useState } from 'react';

const NS = 'http://www.w3.org/2000/svg';

function useDiagram({ condensadora, evaporador, configuracoesMontagem, cavaleteResult, temTanque }) {
  const svgRef = useRef(null);

  const cfg = configuracoesMontagem || {};
  const GE = cfg.incluir_gbc_entrada !== false;
  const FI = cfg.incluir_filtro !== false;
  const VI = cfg.incluir_visor !== false;
  const GS = cfg.incluir_gbc_saida !== false;
  const TQ = !!temTanque;

  const UC = {
    modelo:     condensadora?.modelo     || '—',
    fabricante: condensadora?.fabricante || '',
    liq:        condensadora?.conexao_liquido || '—',
    suc:        condensadora?.conexao_succao  || '—',
  };
  const EV = {
    modelo:     evaporador?.modelo     || '—',
    fabricante: evaporador?.fabricante || '',
    liq:        evaporador?.conexao_liquido || '—',
    suc:        evaporador?.conexao_succao  || '—',
  };

  const cfg_cav = cavaleteResult?.configuracao || {};
  const BL = cfg_cav.diametro_liquido || '—';
  const BS = cfg_cav.diametro_succao  || '—';

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    svg.innerHTML = '';
    const g = document.createElementNS(NS, 'g');
    svg.appendChild(g);

    const mk = (tag, attrs) => {
      const e = document.createElementNS(NS, tag);
      for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
      g.appendChild(e); return e;
    };
    const T = (x, y, s, sz = 9, fill = '#94a3b8', bold = false, anchor = 'middle') => {
      const e = mk('text', { x, y, 'text-anchor': anchor, 'font-size': sz, fill,
        'font-weight': bold ? '800' : '500', 'font-family': 'Segoe UI,system-ui,sans-serif' });
      e.textContent = s; return e;
    };
    const norm = b => (b || '').replace(/[""]/g, '"').trim();

    // Layout — aumentamos viewBox para 460px para caber labels abaixo dos equipamentos
    const Y_LIQ = 85, Y_SUC = 210, Y_SIF = 305, Y_CSF = 143, R = 11;
    const X_UC = 96, X_EV = 896;
    const X_SIF_R = 858, X_MID = 826, X_CSF_D = 794;
    const X_TQ = 152;
    const CX = { gbc_e: 248, fi: 398, sol: 516, vi: 630, vet: 748 };

    // ── UC — ícone compacto sem placa de dados interna ─────────────────
    const drawUC = () => {
      const x = 8, y = 16, w = 86, h = 230;
      mk('rect', { x, y, width: w, height: h, rx: 8, fill: '#071422', stroke: '#0ea5e9', 'stroke-width': 2.5 });
      // Grade superior
      mk('rect', { x: x+4, y: y+4, width: w-8, height: 78, rx: 5, fill: '#050f1c', stroke: '#0a2030', 'stroke-width': 1 });
      for (let i = 0; i < 5; i++) mk('line', { x1: x+6, y1: y+14+i*12, x2: x+w-6, y2: y+14+i*12, stroke: '#0d2540', 'stroke-width': 1.8 });
      // Ventilador
      const fx = x+w/2, fy = y+44;
      mk('circle', { cx: fx, cy: fy, r: 26, fill: '#040c18', stroke: '#1d4ed8', 'stroke-width': 1.5 });
      mk('circle', { cx: fx, cy: fy, r: 5, fill: '#38bdf8' });
      for (let i = 0; i < 4; i++) {
        const a1 = (i*90-40)*Math.PI/180, a2 = (i*90+40)*Math.PI/180;
        mk('path', { d: `M${fx},${fy} C${fx+22*Math.cos(a1)},${fy+22*Math.sin(a1)} ${fx+22*Math.cos(a2)},${fy+22*Math.sin(a2)} ${fx},${fy}`, fill: '#1d4ed8', opacity: '0.65' });
      }
      // Serpentina
      mk('rect', { x: x+4, y: y+86, width: w-8, height: 44, rx: 3, fill: '#050f1c', stroke: '#0a2030', 'stroke-width': 1 });
      for (let i = 0; i < 5; i++) mk('line', { x1: x+6, y1: y+94+i*7, x2: x+w-6, y2: y+94+i*7, stroke: '#122545', 'stroke-width': 1.2 });
      // Compressor
      mk('rect', { x: x+4, y: y+134, width: w-8, height: 76, rx: 3, fill: '#050f1c', stroke: '#0a2030', 'stroke-width': 1 });
      mk('ellipse', { cx: x+w/2, cy: y+172, rx: 22, ry: 28, fill: '#030b16', stroke: '#1e293b', 'stroke-width': 2 });
      mk('ellipse', { cx: x+w/2, cy: y+167, rx: 14, ry: 18, fill: '#09162a', stroke: '#334155', 'stroke-width': 1.5 });
      T(x+w/2, y+171, 'COMP', 7.5, '#4a5568', true);
      // Stubs de conexão
      mk('rect', { x: x+w-1, y: Y_LIQ-5, width: 10, height: 10, rx: 2, fill: '#2563eb' });
      mk('rect', { x: x+w-1, y: Y_SUC-5, width: 10, height: 10, rx: 2, fill: '#7c3aed' });
      // ── Labels abaixo do equipamento ──────────────────────────────────
      const by = y + h + 8;
      T(x+w/2, by,    'U. CONDENSADORA', 7.5, '#38bdf8', true);
      T(x+w/2, by+12, UC.fabricante,     7,   '#475569');
      T(x+w/2, by+23, UC.modelo,         8,   '#93c5fd', true);
      // Bitolas (pequenas tags abaixo do nome)
      mk('rect', { x: x+2, y: by+28, width: 38, height: 13, rx: 3, fill: '#071e38', stroke: '#2563eb', 'stroke-width': 1 });
      T(x+21, by+38, `Liq ${UC.liq}`, 6.5, '#60a5fa', true);
      mk('rect', { x: x+46, y: by+28, width: 38, height: 13, rx: 3, fill: '#1a0840', stroke: '#7c3aed', 'stroke-width': 1 });
      T(x+65, by+38, `Suc ${UC.suc}`, 6.5, '#a78bfa', true);
    };

    // ── Evaporador — ícone compacto sem placa de dados interna ─────────
    const drawEvap = () => {
      const x = X_EV, y = 28, w = 90, h = 210;
      mk('rect', { x, y, width: w, height: h, rx: 8, fill: '#0d0620', stroke: '#6366f1', 'stroke-width': 2.5 });
      // Serpentina/aletas
      mk('rect', { x: x+4, y: y+4, width: w-8, height: 118, rx: 5, fill: '#080318', stroke: '#1e1060', 'stroke-width': 1 });
      for (let i = 0; i < 11; i++) mk('line', { x1: x+8+i*7, y1: y+8, x2: x+8+i*7, y2: y+118, stroke: '#1e1060', 'stroke-width': 1.8 });
      for (let i = 0; i < 5; i++) mk('path', { d: `M${x+8},${y+18+i*18} Q${x+w/2},${y+11+i*18} ${x+w-8},${y+18+i*18}`, fill: 'none', stroke: '#312e81', 'stroke-width': 2 });
      // Bandeja
      mk('rect', { x: x+5, y: y+121, width: w-10, height: 6, rx: 2, fill: '#0a0420', stroke: '#1e1060', 'stroke-width': 1 });
      // Ventilador
      mk('rect', { x: x+4, y: y+130, width: w-8, height: 60, rx: 3, fill: '#080318', stroke: '#1e1060', 'stroke-width': 1 });
      const fx = x+w/2, fy = y+160;
      mk('circle', { cx: fx, cy: fy, r: 22, fill: '#050118', stroke: '#312e81', 'stroke-width': 1.5 });
      mk('circle', { cx: fx, cy: fy, r: 4, fill: '#6366f1' });
      for (let i = 0; i < 4; i++) {
        const a1 = (i*90-38)*Math.PI/180, a2 = (i*90+38)*Math.PI/180;
        mk('path', { d: `M${fx},${fy} C${fx+17*Math.cos(a1)},${fy+17*Math.sin(a1)} ${fx+17*Math.cos(a2)},${fy+17*Math.sin(a2)} ${fx},${fy}`, fill: '#3730a3', opacity: '0.7' });
      }
      // Stubs
      mk('rect', { x: x-9, y: Y_LIQ-5, width: 10, height: 10, rx: 2, fill: '#2563eb' });
      mk('rect', { x: x-9, y: Y_SUC-5, width: 10, height: 10, rx: 2, fill: '#7c3aed' });

      // ── Labels abaixo do equipamento ────────────────────────────────
      const by = y + h + 8;
      T(x+w/2, by,    'EVAPORADOR',   7.5, '#a5b4fc', true);
      T(x+w/2, by+12, EV.fabricante,  7,   '#475569');
      T(x+w/2, by+23, EV.modelo,      8,   '#c4b5fd', true);
      mk('rect', { x: x+4,    y: by+28, width: 38, height: 13, rx: 3, fill: '#071e38', stroke: '#2563eb', 'stroke-width': 1 });
      T(x+23,   by+38, `Liq ${EV.liq}`, 6.5, '#60a5fa', true);
      mk('rect', { x: x+48,   y: by+28, width: 38, height: 13, rx: 3, fill: '#1a0840', stroke: '#7c3aed', 'stroke-width': 1 });
      T(x+67,   by+38, `Suc ${EV.suc}`, 6.5, '#a78bfa', true);

      // Etiquetas de bitola NAS CONEXÕES (lado esquerdo, sem o nome do modelo)
      mk('rect', { x: x-50, y: Y_LIQ-10, width: 40, height: 14, rx: 3, fill: '#0a2040', stroke: '#2563eb', 'stroke-width': 1 });
      T(x-30, Y_LIQ+1, EV.liq, 7.5, '#60a5fa', true);
      mk('rect', { x: x-50, y: Y_SUC+4,  width: 40, height: 14, rx: 3, fill: '#1a0840', stroke: '#7c3aed', 'stroke-width': 1 });
      T(x-30, Y_SUC+15, EV.suc, 7.5, '#a78bfa', true);
    };

    // ── Tanque cilíndrico ─────────────────────────────────────────────
    const drawTanque = () => {
      if (!TQ) return;
      const tx = X_TQ, ty = Y_LIQ-14, tw = 22, th = 68;
      mk('line', { x1: X_UC+9, y1: Y_LIQ, x2: tx-tw/2, y2: Y_LIQ, stroke: '#2563eb', 'stroke-width': 5, 'stroke-linecap': 'round' });
      mk('rect', { x: tx-tw/2, y: ty, width: tw, height: th, rx: 5, fill: '#0a1828', stroke: '#2563eb', 'stroke-width': 2 });
      mk('ellipse', { cx: tx, cy: ty,    rx: tw/2, ry: 5, fill: '#0d2040', stroke: '#2563eb', 'stroke-width': 1.5 });
      mk('ellipse', { cx: tx, cy: ty+th, rx: tw/2, ry: 5, fill: '#0d2040', stroke: '#2563eb', 'stroke-width': 1.5 });
      mk('line', { x1: tx-tw/2+3, y1: ty+th*0.45, x2: tx+tw/2-3, y2: ty+th*0.45, stroke: '#1d4ed8', 'stroke-width': 1, 'stroke-dasharray': '3,2' });
      T(tx, ty+th+14, 'Tanque',  7, '#60a5fa', true);
      T(tx, ty+th+23, 'Líquido', 6.5, '#3b82f6');
      mk('line', { x1: tx+tw/2, y1: Y_LIQ, x2: tx+tw/2+12, y2: Y_LIQ, stroke: '#2563eb', 'stroke-width': 5, 'stroke-linecap': 'round' });
    };

    const comp = (x, lbl, sub, bit, fc, sc, off) => {
      const bw = 62, bh = 50, bx = x-31, by = Y_LIQ+10;
      mk('line', { x1: x, y1: Y_LIQ, x2: x, y2: by, stroke: off ? '#1f2937' : sc, 'stroke-width': 1.5 });
      mk('rect', { x: bx, y: by, width: bw, height: bh, rx: 5, fill: off ? '#070d18' : fc, stroke: off ? '#1f2937' : sc, 'stroke-width': 1.5, 'stroke-dasharray': off ? '4,3' : 'none' });
      T(x, by+17, lbl, 9, off ? '#374151' : '#f0f9ff', !off);
      if (sub) T(x, by+29, sub, 7.5, off ? '#1e2a38' : '#8fb3cc');
      T(x, by+43, off ? 'incluso UC' : bit, 7, off ? '#1e2a38' : '#60a5fa');
    };

    const redAtual = (x, y, de, para, ab = true) => {
      if (norm(de) === norm(para)) return;
      mk('circle', { cx: x, cy: y, r: 7, fill: '#f97316', stroke: '#fdba74', 'stroke-width': 1.5 });
      T(x, ab ? y-12 : y+18, `${de}→${para}`, 7, '#fb923c', true);
    };

    const porca = (x, y) => mk('circle', { cx: x, cy: y, r: 5.5, fill: '#92400e', stroke: '#f59e0b', 'stroke-width': 1.5 });
    const luva  = (x, y) => mk('rect', { x: x-7, y: y-4, width: 14, height: 8, rx: 2, fill: '#0e2040', stroke: '#3b82f6', 'stroke-width': 1.2 });

    drawUC(); drawEvap();

    // ── Linha de Líquido ──────────────────────────────────────────────
    const X_LIQ_START = TQ ? X_TQ+11+12 : X_UC+9;
    mk('line', { x1: X_LIQ_START, y1: Y_LIQ, x2: X_EV-9, y2: Y_LIQ, stroke: '#2563eb', 'stroke-width': 5, 'stroke-linecap': 'round' });
    if (!TQ) mk('line', { x1: X_UC+9, y1: Y_LIQ, x2: X_LIQ_START+30, y2: Y_LIQ, stroke: '#2563eb', 'stroke-width': 5, 'stroke-linecap': 'round' });
    drawTanque();

    T(490, Y_LIQ-16, `→  Linha de Líquido  ${BL}`, 8.5, '#60a5fa', true);
    redAtual(X_UC+52, Y_LIQ, UC.liq, BL, true);

    comp(CX.gbc_e, 'GBC',       'Entrada',   BL,     '#081c38', '#0ea5e9', !GE);
    comp(CX.fi,    'Filtro',    'DML/DMC',   BL,     '#07202e', '#06b6d4', !FI);
    comp(CX.sol,   'Solenoide', 'EVR',       BL,     '#110d30', '#8b5cf6', false);
    comp(CX.vi,    'Visor',     'SGN',       BL,     '#07202e', '#06b6d4', !VI);
    comp(CX.vet,   'VET',       '3/8"→1/2"','3/8"', '#1a0e02', '#f59e0b', false);
    porca(CX.vet-10, Y_LIQ); porca(CX.vet+10, Y_LIQ);
    luva(348, Y_LIQ); luva(672, Y_LIQ);
    redAtual(X_EV-52, Y_LIQ, '1/2"', EV.liq, true);

    // ── Linha de Sucção ───────────────────────────────────────────────
    const C = '#9333ea', SW = 5;
    mk('line', { x1: X_EV-9, y1: Y_SUC, x2: X_SIF_R+R, y2: Y_SUC, stroke: C, 'stroke-width': SW, 'stroke-linecap': 'round' });
    mk('path', {
      d: `M ${X_SIF_R+R} ${Y_SUC}
         Q ${X_SIF_R} ${Y_SUC} ${X_SIF_R} ${Y_SUC+R}
         L ${X_SIF_R} ${Y_SIF-R}
         Q ${X_SIF_R} ${Y_SIF} ${X_SIF_R-R} ${Y_SIF}
         L ${X_MID+R} ${Y_SIF}
         Q ${X_MID} ${Y_SIF} ${X_MID} ${Y_SIF-R}
         L ${X_MID} ${Y_CSF+R}
         Q ${X_MID} ${Y_CSF} ${X_MID-R} ${Y_CSF}
         L ${X_CSF_D+R} ${Y_CSF}
         Q ${X_CSF_D} ${Y_CSF} ${X_CSF_D} ${Y_CSF+R}
         L ${X_CSF_D} ${Y_SUC-R}
         Q ${X_CSF_D} ${Y_SUC} ${X_CSF_D-R} ${Y_SUC}`,
      fill: 'none', stroke: C, 'stroke-width': SW, 'stroke-linecap': 'round', 'stroke-linejoin': 'round',
    });
    mk('line', { x1: X_CSF_D-R, y1: Y_SUC, x2: X_UC+9, y2: Y_SUC, stroke: C, 'stroke-width': SW, 'stroke-linecap': 'round' });

    // Labels sifão
    const sif_cx = (X_SIF_R+X_MID)/2;
    mk('rect', { x: sif_cx-24, y: Y_SIF+8, width: 48, height: 30, rx: 4, fill: '#041a0e', stroke: '#10b981', 'stroke-width': 1.2 });
    T(sif_cx, Y_SIF+21, 'Sifão',  8.5, '#6ee7b7', true);
    T(sif_cx, Y_SIF+30, BS,       7,   '#34d399');
    T(X_MID-14, (Y_SIF+Y_CSF)/2, 'Subida', 7, '#22d3ee', false, 'middle');
    const csf_cx = (X_MID+X_CSF_D)/2;
    mk('rect', { x: csf_cx-30, y: Y_CSF-36, width: 60, height: 30, rx: 4, fill: '#041a0e', stroke: '#10b981', 'stroke-width': 1.2 });
    T(csf_cx, Y_CSF-22, 'Contra-sifão', 8, '#6ee7b7', true);
    T(csf_cx, Y_CSF-12, BS,             7, '#34d399');

    // GBC Saída inline
    const GS_X = Math.round((X_CSF_D-R+X_UC+9)/2);
    mk('rect', { x: GS_X-32, y: Y_SUC-15, width: 64, height: 30, rx: 5,
      fill: GS ? '#091c38' : '#070d18', stroke: GS ? '#0ea5e9' : '#1f2937',
      'stroke-width': 1.5, 'stroke-dasharray': GS ? 'none' : '4,3' });
    T(GS_X, Y_SUC-2,  'GBC Saída', 8.5, GS ? '#e0f2fe' : '#374151', GS);
    T(GS_X, Y_SUC+10, GS ? BS : 'incluso UC', 7, GS ? '#a78bfa' : '#374151');

    T(460, Y_SUC+55, `←  Linha de Sucção  ${BS}`, 8.5, '#a855f7', true);
    luva(545, Y_SUC); luva(655, Y_SUC);
    redAtual(X_EV-52, Y_SUC, EV.suc, BS, false);
    redAtual(X_UC+52, Y_SUC, BS, UC.suc, false);

    // Setas de fluxo
    mk('polygon', { points: `${462},${Y_LIQ-7} ${473},${Y_LIQ} ${462},${Y_LIQ+7}`, fill: '#3b82f6' });
    mk('polygon', { points: `${477},${Y_SUC-7} ${466},${Y_SUC} ${477},${Y_SUC+7}`, fill: '#9333ea' });

  }, [UC.modelo, UC.liq, UC.suc, EV.modelo, EV.liq, EV.suc, BL, BS, GE, FI, VI, GS, TQ]);

  return svgRef;
}

export default function CavaleteIlustracao({ condensadora, evaporador, configuracoesMontagem, cavaleteResult, temTanque }) {
  const [aberto, setAberto] = useState(false);
  const svgRef = useDiagram({ condensadora, evaporador, configuracoesMontagem, cavaleteResult, temTanque });

  return (
    <>
      {/* Botão flutuante */}
      <button
        onClick={() => setAberto(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2 px-4 py-3 rounded-full shadow-2xl
          bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold transition-all
          border border-slate-600 hover:border-sky-500 hover:shadow-sky-900/40"
        title="Ver diagrama de tubulação"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 12h4M17 12h4M12 3v4M12 17v4"/>
          <circle cx="12" cy="12" r="3"/>
          <path d="M7 12H3M21 12h-4M12 7V3M12 21v-4"/>
        </svg>
        Diagrama Cavalete
      </button>

      {/* Modal flutuante */}
      {aberto && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Overlay */}
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setAberto(false)} />

          {/* Painel */}
          <div className="relative w-full max-w-5xl bg-[#07111e] rounded-2xl shadow-2xl border border-slate-700 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3 bg-[#060f1c] border-b border-slate-800">
              <div className="flex items-center gap-3">
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">
                  Cavalete de Componentes — Diagrama de Tubulação
                </span>
                <div className="flex gap-3 text-[8px] text-slate-600">
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-3 h-1.5 rounded bg-blue-500"/>Líquido
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-3 h-1.5 rounded bg-purple-500"/>Sucção
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-2 h-2 rounded-full bg-orange-400"/>Redução
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-3 h-1.5 rounded border border-dashed border-slate-600"/>Incluso UC
                  </span>
                </div>
              </div>
              <button
                onClick={() => setAberto(false)}
                className="text-slate-500 hover:text-white text-lg leading-none transition-colors"
              >✕</button>
            </div>

            {/* SVG */}
            <svg
              ref={svgRef}
              viewBox="0 0 1000 420"
              xmlns="http://www.w3.org/2000/svg"
              className="w-full"
            />
          </div>
        </div>
      )}
    </>
  );
}
