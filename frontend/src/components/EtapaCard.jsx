/**
 * EtapaCard — Card colapsável para o wizard de dimensionamento.
 *
 * Importante: children são SEMPRE montados (nunca desmontados),
 * apenas escondidos via CSS. Isso preserva o estado interno do componente
 * ao fechar/reabrir sem perder dados.
 *
 * status:
 *   'concluido'  → etapa finalizada, mostra resumo colapsado (verde)
 *   'disponivel' → etapa acessível mas ainda não concluída (slate)
 *   'bloqueado'  → etapa anterior não concluída, não clicável (cinza)
 */
const EtapaCard = ({
  numero,
  titulo,
  icone,
  status,        // 'concluido' | 'disponivel' | 'bloqueado'
  resumo,        // string exibido quando concluido e colapsado
  selecionado,   // boolean — card está selecionado (detalhe visível à direita)
  expandido,     // boolean — card está aberto para edição
  onSelecionar,  // () => void — clique no header: mostra detalhe, NÃO abre
  onEditar,      // () => void — clique em "Editar": abre para edição
  onFechar,      // () => void — clique em "Descartar edição": fecha sem perder dados
  somenteLeitura,// boolean — card final (ex: Orçamento): sem botões Editar/Descartar
  children,
}) => {

  const clicavelHeader = status !== 'bloqueado';

  // Estilo da borda do card
  const bordaCard = expandido
    ? 'border-[#7B2D8B] shadow-lg shadow-purple-100'
    : selecionado
      ? 'border-[#7B2D8B]/40 shadow-sm shadow-purple-50'
      : status === 'concluido'
        ? 'border-emerald-300 hover:border-emerald-400'
        : status === 'disponivel'
          ? 'border-slate-200 hover:border-slate-300'
          : 'border-slate-200 bg-slate-50';   // bloqueado

  // Badge numérico
  const estiloBadge = expandido
    ? 'bg-[#7B2D8B] text-white'
    : status === 'concluido'
      ? 'bg-emerald-500 text-white'
      : status === 'disponivel'
        ? 'bg-slate-300 text-slate-600'
        : 'bg-slate-200 text-slate-400';    // bloqueado

  // Para cards somenteLeitura: header clica abre/fecha diretamente
  const handleHeaderClick = () => {
    if (!clicavelHeader) return;
    if (somenteLeitura) {
      expandido ? onFechar() : onEditar();
    } else {
      onSelecionar();
    }
  };

  return (
    <div className={`rounded-xl border-2 bg-white transition-all duration-300 ${bordaCard}`}>

      {/* ── Cabeçalho ── sempre visível ── */}
      <div
        className={`flex items-center justify-between px-5 py-4 select-none
          ${clicavelHeader ? 'cursor-pointer' : ''}
          ${status === 'bloqueado' ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        onClick={handleHeaderClick}
      >
        {/* Esquerda: badge + título + resumo */}
        <div className="flex items-center gap-3 min-w-0">
          <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center font-bold text-sm transition-all ${estiloBadge}`}>
            {status === 'concluido' && !expandido ? '✓' : numero}
          </div>

          <div className="min-w-0">
            <p className={`text-sm font-black uppercase tracking-wide leading-tight ${
              status === 'bloqueado' ? 'text-slate-400' : 'text-slate-700'
            }`}>
              {icone} {titulo}
            </p>
            {/* Resumo apenas quando concluído e fechado */}
            {status === 'concluido' && !expandido && resumo && (
              <p className="text-xs text-slate-500 font-medium mt-0.5 truncate max-w-sm">
                {resumo}
              </p>
            )}
          </div>
        </div>

        {/* Direita: ações */}
        <div className="flex items-center gap-2 flex-shrink-0 ml-4">

          {/* Botão Editar — apenas para cards editáveis */}
          {!somenteLeitura && status === 'concluido' && !expandido && (
            <button
              onClick={e => { e.stopPropagation(); onEditar(); }}
              className="text-xs font-bold px-3 py-1.5 rounded-lg border border-[#7B2D8B] text-[#7B2D8B] hover:bg-purple-50 transition-all"
            >
              ✏️ Editar
            </button>
          )}

          {/* Botão Descartar — apenas para cards editáveis */}
          {!somenteLeitura && expandido && (
            <button
              onClick={e => { e.stopPropagation(); onFechar(); }}
              className="text-xs font-bold px-3 py-1.5 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50 transition-all"
            >
              ✕ Descartar edição
            </button>
          )}

          {/* Chevron para somenteLeitura (abre/fecha pelo header) */}
          {somenteLeitura && status !== 'bloqueado' && (
            <span className="text-slate-400 text-sm font-bold">
              {expandido ? '▲' : '▼'}
            </span>
          )}

          {/* Lock */}
          {status === 'bloqueado' && (
            <span className="text-slate-300 text-base select-none">🔒</span>
          )}

          {/* Indicador de selecionado (sem edição) */}
          {!expandido && selecionado && status !== 'bloqueado' && (
            <span className="w-2 h-2 rounded-full bg-[#7B2D8B] animate-pulse"/>
          )}

          {/* Chevron: disponível, não selecionado, não expandido */}
          {status === 'disponivel' && !expandido && !selecionado && (
            <span className="text-slate-400 text-sm">▼</span>
          )}
        </div>
      </div>

      {/* ── Conteúdo ── SEMPRE montado, escondido via CSS quando colapsado ── */}
      <div className={expandido ? 'border-t border-slate-100' : 'hidden'}>
        {children}
      </div>

    </div>
  );
};

export default EtapaCard;
