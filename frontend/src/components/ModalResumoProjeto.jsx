import { CheckCircle2, AlertTriangle, ChevronRight, FileText, Thermometer, Zap, GitBranch, Settings2, ShoppingCart } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const CARDS = [
  { num: 1, label: 'Gabinete',            icon: <FileText    className="w-4 h-4" /> },
  { num: 2, label: 'Carga Térmica',       icon: <Thermometer className="w-4 h-4" /> },
  { num: 3, label: 'Equipamentos',        icon: <Zap         className="w-4 h-4" /> },
  { num: 4, label: 'Tubulação',           icon: <GitBranch   className="w-4 h-4" /> },
  { num: 5, label: 'Componentes',         icon: <Settings2   className="w-4 h-4" /> },
  { num: 6, label: 'Orçamento',           icon: <ShoppingCart className="w-4 h-4" /> },
]

function statusCard(num, dados) {
  if (num === 1) return dados.gabinete ? 'concluido' : 'pendente'
  if (num === 2) return dados.carga_termica ? 'concluido' : 'pendente'
  if (num === 3) return dados.orcamento?.equipamentos?.length ? 'concluido' : 'pendente'
  if (num === 4) return (dados.itens_tubulacao?.length || dados.resultado_tubulacao) ? 'concluido' : 'pendente'
  if (num === 5) return dados.itens_acessorios?.length ? 'concluido' : 'pendente'
  if (num === 6) return (dados.orcamento?.materiais?.length || dados.orcamento?.equipamentos?.length) ? 'concluido' : 'pendente'
  return 'pendente'
}

export default function ModalResumoProjeto({ projeto, dados, onIrParaOrcamento, onRevisar }) {
  if (!projeto || !dados) return null

  const d = dados.dados_completos || {}

  // Monta resumo de valores
  const gabinete = d.gabinete
  const carga    = d.carga_termica
  const equips   = d.orcamento?.equipamentos || []
  const tubulacao = d.resultado_tubulacao
  const acessorios = d.itens_acessorios || []

  const uc   = equips.find(e => e.categoria?.toLowerCase().includes('condensa') || e.tipo === 'UC')
  const evap = equips.find(e => e.categoria?.toLowerCase().includes('evapora') || e.tipo === 'Evap')

  const cardsConcluidos = CARDS.filter(c => statusCard(c.num, d) === 'concluido').length
  const temOrcamento = statusCard(6, d) === 'concluido'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">

        {/* Header */}
        <div className="bg-primary/5 border-b border-border px-6 py-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold text-primary uppercase tracking-widest mb-1">Projeto carregado</p>
              <h2 className="text-lg font-semibold text-foreground leading-tight">{projeto.nome}</h2>
              {projeto.cliente && (
                <p className="text-sm text-muted-foreground mt-0.5">Cliente: {projeto.cliente}</p>
              )}
            </div>
            <Badge variant={cardsConcluidos === 6 ? 'success' : 'warning'} className="text-xs flex-shrink-0 mt-1">
              {cardsConcluidos}/6 etapas
            </Badge>
          </div>
        </div>

        {/* Resumo de valores */}
        <div className="px-6 py-4 space-y-3">

          {/* Gabinete */}
          {gabinete && (
            <div className="flex items-start gap-3 text-sm">
              <FileText className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-medium text-foreground">Gabinete: </span>
                <span className="text-muted-foreground">
                  {gabinete.comprimento}m × {gabinete.largura}m × {gabinete.altura}m
                  {gabinete.temperatura_interna != null && ` · T.Int ${gabinete.temperatura_interna}°C`}
                  {gabinete.nucleo && ` · Painel ${gabinete.nucleo}`}
                </span>
              </div>
            </div>
          )}

          {/* Carga térmica */}
          {carga && (
            <div className="flex items-start gap-3 text-sm">
              <Thermometer className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-medium text-foreground">Carga térmica: </span>
                <span className="text-muted-foreground">
                  {Number(carga).toLocaleString('pt-BR')} kcal/h
                </span>
              </div>
            </div>
          )}

          {/* Equipamentos */}
          {equips.length > 0 && (
            <div className="flex items-start gap-3 text-sm">
              <Zap className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-medium text-foreground">Equipamentos: </span>
                <span className="text-muted-foreground">
                  {uc?.modelo || equips[0]?.modelo}
                  {evap && ` · ${evap.modelo}`}
                </span>
              </div>
            </div>
          )}

          {/* Tubulação */}
          {tubulacao && (
            <div className="flex items-start gap-3 text-sm">
              <GitBranch className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-medium text-foreground">Tubulação: </span>
                <span className="text-muted-foreground">
                  Líquido {tubulacao.diametro_liquido || '—'}
                  {tubulacao.diametro_succao && ` · Sucção ${tubulacao.diametro_succao}`}
                </span>
              </div>
            </div>
          )}

          {/* Componentes */}
          {acessorios.length > 0 && (
            <div className="flex items-start gap-3 text-sm">
              <Settings2 className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-medium text-foreground">Componentes: </span>
                <span className="text-muted-foreground">
                  {acessorios.length} itens selecionados
                </span>
              </div>
            </div>
          )}

          {/* Status dos cards */}
          <div className="pt-1 border-t border-border">
            <div className="flex flex-wrap gap-2 mt-2">
              {CARDS.map(c => {
                const st = statusCard(c.num, d)
                return (
                  <div key={c.num} className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${
                    st === 'concluido'
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                      : 'bg-muted/50 border-border text-muted-foreground'
                  }`}>
                    {st === 'concluido'
                      ? <CheckCircle2 className="w-3 h-3" />
                      : <AlertTriangle className="w-3 h-3" />
                    }
                    {c.label}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Instrução */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-xs text-blue-800 leading-relaxed">
            <strong>Como prosseguir:</strong> se o projeto está correto, vá direto ao orçamento.
            Se precisar ajustar algo, clique em <em>Revisar projeto</em> e edite o card desejado —
            o sistema avisará quais etapas podem ser afetadas.
          </div>
        </div>

        {/* Ações */}
        <div className="border-t border-border px-6 py-4 flex items-center justify-between gap-3">
          <Button variant="outline" onClick={onRevisar} className="gap-2">
            Revisar projeto
          </Button>
          <Button
            onClick={onIrParaOrcamento}
            disabled={!temOrcamento}
            className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            Ir para o Orçamento <ChevronRight className="w-4 h-4" />
          </Button>
        </div>

        {!temOrcamento && (
          <p className="text-center text-xs text-muted-foreground pb-3 -mt-2">
            Conclua todas as etapas para gerar o orçamento
          </p>
        )}
      </div>
    </div>
  )
}
