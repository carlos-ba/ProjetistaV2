import React, { useState } from 'react';
import DENSIDADE_PRODUTOS from '../data/densidadeProdutos';

// Insight informativo — estimativa grosseira de capacidade a partir do volume da
// câmara e da densidade de um produto de referência. NUNCA usar este valor no
// cálculo de carga térmica (isso já é feito à parte, pela seleção real do Card 2).
const InsightCapacidadeEstimada = ({ volumeM3 }) => {
  const [produtoNome, setProdutoNome] = useState('');

  if (!volumeM3 || volumeM3 <= 0) return null;

  const produto = DENSIDADE_PRODUTOS.find(p => p.nome === produtoNome);
  const cargaMaxima  = produto ? Math.round(volumeM3 * produto.densidade * 0.7) : null;
  const cargaRotativa = cargaMaxima != null ? Math.round(cargaMaxima * 0.3) : null;

  return (
    <div className="p-3 rounded-lg border-l-4 bg-white shadow-sm" style={{ borderLeftColor: '#3498db' }}>
      <strong className="block text-[11px] uppercase tracking-tight" style={{ color: '#3498db' }}>
        Estimativa de Capacidade
      </strong>
      <select
        value={produtoNome}
        onChange={e => setProdutoNome(e.target.value)}
        className="mt-1.5 w-full text-[10px] px-1.5 py-1 rounded border border-slate-200 bg-white outline-none focus:ring-1 focus:ring-blue-400"
      >
        <option value="">Produto de referência...</option>
        {DENSIDADE_PRODUTOS.map(p => (
          <option key={p.nome} value={p.nome}>{p.nome} — {p.densidade.toLocaleString('pt-BR')} kg/m³</option>
        ))}
      </select>
      {produto && (
        <p className="text-xs text-slate-600 leading-tight mt-1.5">
          ~{cargaMaxima.toLocaleString('pt-BR')} kg de carga máxima ·
          ~{cargaRotativa.toLocaleString('pt-BR')} kg/dia de carga rotativa
        </p>
      )}
      <p className="text-[9px] text-slate-400 italic leading-tight mt-1.5">
        Só uma ideia aproximada de movimentação — nunca use este número no cálculo de carga térmica.
      </p>
    </div>
  );
};

export default InsightCapacidadeEstimada;
