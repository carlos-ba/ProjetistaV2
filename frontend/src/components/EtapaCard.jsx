import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CheckCircle2, Lock, Pencil, ChevronDown, ChevronUp, ChevronRight, AlertTriangle } from "lucide-react"

const EtapaCard = ({
  numero,
  titulo,
  icone,
  status,
  resumo,
  selecionado,
  expandido: expandidoProp,
  onSelecionar,
  onEditar,
  onFechar,
  somenteLeitura,
  bloqueadoTrial,     // bool — avaliação encerrada: impede entrar em modo de edição
  invalidado,         // bool — exibe aviso de "pode estar desatualizado"
  confirmacaoProxima, // string com nome da próxima etapa (ou null)
  onConfirmar,        // () => void — avança para próxima etapa
  onRecusar,          // () => void — fica na etapa atual
  children,
}) => {

  // Com trial vencido, o card nunca renderiza expandido — mesmo que já tivesse
  // aberto por padrão (ex: Card 1 de um projeto novo/incompleto, sem precisar
  // de clique em "Editar" pra chegar lá).
  const expandido = bloqueadoTrial ? false : expandidoProp

  const clicavelHeader = status !== 'bloqueado'

  const handleHeaderClick = () => {
    if (!clicavelHeader) return
    if (bloqueadoTrial && status !== 'concluido') return
    if (somenteLeitura || status !== 'concluido') {
      // Etapa ainda não concluída não tem botão "Editar" separado — sem isso, recolher
      // o card (Descartar/Recolher) antes de terminar deixava sem nenhum jeito de reabrir.
      expandido ? onFechar() : onEditar()
    } else {
      onSelecionar()
    }
  }

  return (
    <div className={cn(
      "rounded-xl border bg-card text-card-foreground shadow-sm transition-all duration-300",
      expandido     && "border-primary shadow-md shadow-primary/10",
      selecionado   && !expandido && "border-primary/30",
      status === 'bloqueado' && "opacity-60 bg-muted/30",
    )}>

      {/* ── Cabeçalho ── */}
      <div
        className={cn(
          "flex items-center justify-between px-5 py-4 select-none",
          clicavelHeader && "cursor-pointer",
          status === 'bloqueado' && "cursor-not-allowed",
          bloqueadoTrial && status !== 'concluido' && !expandido && "cursor-not-allowed",
        )}
        onClick={handleHeaderClick}
      >
        {/* Esquerda */}
        <div className="flex items-center gap-3 min-w-0">
          {/* Badge */}
          <div className={cn(
            "w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-bold transition-all",
            expandido             ? "bg-primary text-primary-foreground"
            : status === 'concluido' ? "bg-emerald-500 text-white"
            : status === 'disponivel'? "bg-muted text-muted-foreground border border-border"
            : "bg-muted text-muted-foreground"
          )}>
            {status === 'concluido' && !expandido
              ? <CheckCircle2 className="w-4 h-4" />
              : numero
            }
          </div>

          {/* Título + resumo */}
          <div className="min-w-0">
            <p className={cn(
              "text-sm font-semibold leading-tight",
              status === 'bloqueado' ? "text-muted-foreground" : "text-foreground"
            )}>
              {icone} {titulo}
            </p>
            {status === 'concluido' && !expandido && resumo && (
              <p className="text-xs text-muted-foreground mt-0.5 truncate max-w-sm">{resumo}</p>
            )}
          </div>
        </div>

        {/* Direita — ações */}
        <div className="flex items-center gap-2 flex-shrink-0 ml-4">

          {/* Status badge */}
          {status === 'concluido' && !expandido && (
            <Badge variant="success" className="text-[10px] hidden sm:flex">Concluído</Badge>
          )}

          {/* Aviso de desatualizado — etapa anterior recalculou depois desta */}
          {status === 'concluido' && !expandido && invalidado && (
            <Badge variant="warning" className="text-[10px] hidden sm:flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> Pode estar desatualizado
            </Badge>
          )}

          {/* Botão Editar */}
          {!somenteLeitura && !bloqueadoTrial && status === 'concluido' && !expandido && (
            <Button
              variant="outline" size="sm"
              onClick={e => { e.stopPropagation(); onEditar() }}
              className="h-7 text-xs gap-1"
            >
              <Pencil className="w-3 h-3" /> Editar
            </Button>
          )}

          {/* Avaliação encerrada — só visualização, sem botão de editar */}
          {bloqueadoTrial && status === 'concluido' && !expandido && (
            <Lock className="w-4 h-4 text-muted-foreground/40" title="Avaliação encerrada — assine um plano para editar" />
          )}

          {/* Botão Recolher — só fecha o card, não apaga nada preenchido/calculado */}
          {!somenteLeitura && expandido && (
            <Button
              variant="ghost" size="sm"
              onClick={e => { e.stopPropagation(); onFechar() }}
              className="h-7 text-xs gap-1 text-muted-foreground"
              title="Recolhe o card — o que já foi preenchido ou calculado continua salvo"
            >
              <ChevronUp className="w-3 h-3" /> Recolher
            </Button>
          )}

          {/* Lock */}
          {status === 'bloqueado' && <Lock className="w-4 h-4 text-muted-foreground/40" />}

          {/* Ponto selecionado */}
          {!expandido && selecionado && status !== 'bloqueado' && (
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          )}

          {/* Chevron somenteLeitura */}
          {somenteLeitura && status !== 'bloqueado' && (
            expandido
              ? <ChevronUp className="w-4 h-4 text-muted-foreground" />
              : <ChevronDown className="w-4 h-4 text-muted-foreground" />
          )}

          {/* Chevron disponível */}
          {status === 'disponivel' && !expandido && !selecionado && !bloqueadoTrial && (
            <ChevronDown className="w-4 h-4 text-muted-foreground" />
          )}

          {/* Avaliação encerrada — etapa ainda incompleta, sem jeito de continuar editando */}
          {bloqueadoTrial && status === 'disponivel' && !expandido && (
            <Lock className="w-4 h-4 text-muted-foreground/40" title="Avaliação encerrada — assine um plano para editar" />
          )}
        </div>
      </div>


      {/* ── Conteúdo ── sempre montado ── */}
      <div className={cn(
        "border-t border-border",
        expandido ? "block" : "hidden"
      )}>
        {children}
      </div>

      {/* ── Barra de confirmação ── aparece após concluir a etapa ── */}
      {expandido && confirmacaoProxima && (
        <div className="border-t border-emerald-200 bg-emerald-50 px-5 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-emerald-700 text-sm">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>
              Etapa concluída! Avançar para{' '}
              <strong>{confirmacaoProxima}</strong>?
            </span>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Button
              variant="ghost" size="sm"
              onClick={onRecusar}
              className="text-slate-500 hover:text-slate-700 text-xs"
            >
              Continuar aqui
            </Button>
            <Button
              size="sm"
              onClick={onConfirmar}
              className="gap-1 text-xs bg-emerald-600 hover:bg-emerald-700"
            >
              Avançar <ChevronRight className="w-3 h-3" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

export default EtapaCard
