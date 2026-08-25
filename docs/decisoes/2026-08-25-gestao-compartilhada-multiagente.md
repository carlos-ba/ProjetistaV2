# Gestão Compartilhada Multi-Agente (Codex + Claude)

**Data:** 2026-08-25
**Decisão:** Manter o desenvolvimento do ecossistema IceNexus (SaaS + site
institucional) sob gestão compartilhada entre dois agentes de IA — Codex e
Claude Code — usando o GitHub (`carlos-ba/ProjetistaV2`) como fonte única de
verdade, em vez de migrar tudo para uma única ferramenta.

**Motivo:** cada agente já acumulou contexto profundo em domínios diferentes —
Claude no núcleo técnico do SaaS "Projeto de Câmara Fria", Codex na estratégia
comercial, conteúdo e UI/UX do site institucional (`site-ecosistema/`). Migrar
tudo para um só agente jogaria fora contexto real sem necessidade.

---

## Divisão de responsabilidade

| Área | Responsável principal | Revisor |
|------|----|----|
| Estratégia comercial, páginas, conteúdo e jornada (`site-ecosistema/`) | Codex | Claude |
| UI/UX e integração das páginas institucionais | Codex | Claude |
| Núcleo do SaaS (`backend/`, `frontend/`) e suas regras técnicas | Claude | Codex |
| Novas funcionalidades dentro do SaaS atual | Claude (preferencial) | Codex |
| Novas ferramentas independentes | caso a caso, decidido na fase de definição | o outro agente |
| Auditoria, testes e revisão de integração | o outro agente, como revisor | — |

## Regra central

**Uma tarefa → uma branch → um responsável principal.** As duas IAs não editam
simultaneamente os mesmos arquivos na mesma branch — é o que mais gera
conflito, retrabalho e perda de contexto (já observado nesta mesma migração:
`CLAUDE.md` divergiu entre um commit meu e uma limpeza do Codex, exigindo
merge de reconciliação).

Fluxo:
1. Necessidade e critérios são registrados no GitHub (issue, ou entrada em
   `docs/decisoes/` para decisões maiores).
2. Um agente assume a implementação em uma branch.
3. O outro revisa o resultado.
4. Testes e Preview da Vercel são executados antes do merge.
5. Só o trabalho aprovado entra em `main`.
6. A documentação compartilhada (`docs/`) é atualizada.

Arquivos "de todo mundo" (`docs/`, `AGENTS.md`, `CLAUDE.md`) são o maior risco
de conflito justamente por serem compartilhados — mudanças neles devem ser
pequenas e enviadas com frequência, não acumuladas.

## Novas ferramentas — duas fases

**Fase de definição** (produto, antes de decidir quem desenvolve): público,
problema, proposta de valor, oferta, plano Free e assinaturas, jornada de
aquisição, estrutura da página, interface inicial, briefing técnico. Registrar
em `docs/produtos/`.

**Fase de desenvolvimento** (decidida conforme a integração):
- Extensão profunda do Projeto de Câmara Fria → Claude lidera (já conhece o
  núcleo).
- Ferramenta nova, módulo independente, página, portal, simulador ou frontend
  isolado → decidido caso a caso.
- Múltiplas frentes independentes (arquitetura, frontend, testes, revisão) →
  possível dividir entre agentes em paralelo, desde que sejam frentes
  realmente independentes — não vantagem automática em tarefas pequenas ou
  fortemente acopladas.

## Fonte de verdade vs. memória privada de cada agente

Cada agente mantém memória própria (histórico de sessões, atalhos de
contexto) que **não é visível ao outro**. Qualquer decisão ou contexto que o
outro agente precise para trabalhar sem retrabalho vai para `docs/` — memória
privada é acelerador pessoal, nunca fonte de verdade compartilhada.

## Estrutura de `docs/` compartilhada

```
docs/
├── produtos/       — fase de definição de novos produtos/ferramentas
├── arquitetura/     — decisões de arquitetura que atravessam mais de um domínio
├── comercial/       — material comercial e de posicionamento (já existia)
├── decisoes/        — registro de decisões relevantes para os dois agentes
├── casos-de-uso/     — personas e jornadas mapeadas
└── handoffs/         — estado de branches ativas / quem está fazendo o quê agora
```

`AGENTS.md` orienta o Codex e `CLAUDE.md` orienta o Claude — ambos apontam para
os mesmos documentos centrais em `docs/`, evitando duas versões da verdade.

## Pendências abertas desta decisão

- CI mínimo (lint + build) como gate real de PR ainda não existe — hoje cada
  agente roda testes manualmente antes do merge, por disciplina, não por
  automação.
- Vários documentos históricos soltos na raiz do repo (`ANALISE_*.md`,
  `DESIGN_*.md`, não commitados) e a documentação antiga em `docs/*.md`
  (numerada 00-09, checkpoints) ainda não foram migrados para esta nova
  estrutura — reorganização cosmética, não bloqueante, fica para quando algum
  agente tocar nesses temas de novo.
