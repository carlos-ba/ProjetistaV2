# AGENTS.md — ProjetistaV2 / Ecossistema IceNexus

Leia este arquivo no início de toda sessão do Codex neste repositório.

## Fonte da verdade

Este repositório (GitHub, `carlos-ba/ProjetistaV2`) é a fonte única de
verdade, compartilhada entre Codex e Claude Code. Documentação técnica e
operacional completa do SaaS (stack, URLs, ambiente local, migrations,
endpoints, convenções de nomenclatura) está em [`CLAUDE.md`](CLAUDE.md) — vale
igualmente para o Codex, não é conteúdo específico de uma ferramenta.

Decisões de produto/arquitetura compartilhadas entre os dois agentes ficam em
`docs/decisoes/`, não na memória privada de cada agente.

## Gestão compartilhada entre agentes

Ver [`docs/decisoes/2026-08-25-gestao-compartilhada-multiagente.md`](docs/decisoes/2026-08-25-gestao-compartilhada-multiagente.md)
para o modelo completo. Resumo:

| Área | Responsável principal | Revisor |
|------|----|----|
| Estratégia comercial, páginas, conteúdo e jornada (`site-ecosistema/`) | Codex | Claude |
| UI/UX e integração das páginas institucionais | Codex | Claude |
| Núcleo do SaaS (`backend/`, `frontend/`) e suas regras técnicas | Claude | Codex |
| Novas funcionalidades dentro do SaaS atual | Claude (preferencial) | Codex |
| Novas ferramentas independentes | caso a caso | o outro agente |
| Auditoria, testes e revisão de integração | o outro agente, como revisor | — |

**Regra central: uma tarefa → uma branch → um responsável principal.** As duas
IAs não editam simultaneamente os mesmos arquivos na mesma branch.

## Escopo neste repositório

- `site-ecosistema/` — site institucional Next.js (`icenexus.com.br`),
  domínio principal do Codex. Deploy Vercel próprio (`icenexus-site`, Root
  Directory `site-ecosistema`), auto-deploy no push para `main`.
- `backend/`, `frontend/` — SaaS "Projeto de Câmara Fria", domínio principal
  do Claude. Deploy Render (backend) + Vercel (frontend), auto-deploy no push
  para `main`.
- `docs/` — documentação compartilhada, ver estrutura abaixo.

## Estrutura de `docs/` compartilhada

- `docs/produtos/` — fase de definição de novos produtos/ferramentas (público,
  problema, proposta de valor, oferta, planos, jornada, estrutura de página,
  briefing técnico) antes de decidir quem desenvolve.
- `docs/arquitetura/` — decisões de arquitetura que atravessam mais de um
  domínio (ver também `docs/02_arquitetura.md` e `docs/07_decisoes_tecnicas.md`,
  documentação técnica já existente do SaaS — não duplicar).
- `docs/comercial/` — material comercial e de posicionamento (já existente).
- `docs/decisoes/` — registro de decisões relevantes para os dois agentes, um
  arquivo por decisão, datado.
- `docs/casos-de-uso/` — personas e jornadas mapeadas.
- `docs/handoffs/` — estado de branches ativas / o que cada agente está
  fazendo agora, um arquivo por handoff em andamento.

## Regra prática para arquivos compartilhados

`docs/`, `AGENTS.md` e `CLAUDE.md` são os arquivos de maior risco de conflito
por serem editados pelos dois agentes. Antes de editar: `git pull`. Depois de
editar: commit e push pequenos e frequentes, não acumular mudanças — foi
divergir em paralelo que já causou retrabalho nesta migração (ver o registro
de decisão acima).
