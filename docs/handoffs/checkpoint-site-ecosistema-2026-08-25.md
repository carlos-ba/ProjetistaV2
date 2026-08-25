# Checkpoint de retomada — Site institucional IceNexus

**Data:** 2026-08-25  
**Status:** checkpoint documental; nenhuma implementação ativa  
**Responsável principal do domínio:** Codex  
**Revisor preferencial:** Claude

## Objetivo deste registro

Permitir que Codex, Claude ou o usuário retomem o desenvolvimento das páginas
do ecossistema IceNexus sem reconstruir o histórico recente. O GitHub
`carlos-ba/ProjetistaV2` continua sendo a fonte única de verdade.

## Estado confirmado

- Site institucional em `site-ecosistema/` (Next.js).
- Produção: <https://www.icenexus.com.br/>.
- Hospedagem: projeto `icenexus-site` na Vercel, com Root Directory
  `site-ecosistema` e produção vinculada à branch `main`.
- Rotas verificadas com resposta HTTP 200 em 2026-08-25:
  - `/`
  - `/projeto-camara-fria`
  - `/academia`
  - `/acessar`
- O site institucional e o SaaS permanecem no mesmo repositório, mas com
  deploys independentes.

## Commits de referência

- `88b07f7` — merge da correção dos links internos com `next/link`.
- `edd01cd` — instituição da gestão compartilhada Codex + Claude, inclusão do
  `AGENTS.md` e da estrutura central de documentação em `docs/`.

No encerramento deste checkpoint, `edd01cd` estava publicado em `origin/main`.

## Gestão compartilhada vigente

Seguir `AGENTS.md` e
`docs/decisoes/2026-08-25-gestao-compartilhada-multiagente.md`.

Regra central:

> Uma tarefa → uma branch → um responsável principal.

- Codex lidera `site-ecosistema/`: estratégia comercial, conteúdo, UI/UX e
  integração das páginas institucionais.
- Claude lidera `backend/` e `frontend/`: núcleo técnico do SaaS Projeto de
  Câmara Fria.
- O outro agente atua como revisor quando aplicável.
- Decisões necessárias aos dois agentes devem ser registradas em `docs/`, não
  apenas em memórias privadas.

## Qualidade técnica conhecida do site

- Correção de `next/link` confirmada em produção.
- Lint atual: **0 erros e 11 avisos**.
- Os 11 avisos são usos de `<img>` que podem ser migrados gradualmente para o
  componente `Image` do Next.js, com validação visual e responsiva.
- Último `npm audit` conhecido: **3 vulnerabilidades em dependências de
  desenvolvimento**, sendo 1 baixa e 2 altas, sem vulnerabilidade crítica:
  - `@babel/core` — baixa;
  - `brace-expansion` — alta;
  - `js-yaml` — alta.
- Essas dependências chegam pelo ecossistema de lint/build e não integram o
  runtime normal entregue ao visitante. Atualizar em branch isolada, sem usar
  `npm audit fix --force`, e validar lint, build e Preview antes do merge.

## Próximas frentes possíveis

Não há uma implementação escolhida neste checkpoint. Ao retomar, definir uma
frente antes de editar:

1. otimização controlada das imagens do site;
2. atualização segura das dependências de desenvolvimento;
3. evolução de conteúdo e conversão das páginas existentes;
4. novas páginas ou ferramentas, iniciando pela fase de definição em
   `docs/produtos/`;
5. implantação de CI mínimo (lint + build) como gate de PR.

## Cuidados na retomada

- Começar conferindo `git status`, `git log -1` e a branch atual.
- Não incluir nos commits arquivos antigos não rastreados da raiz, planilhas,
  pastas `R22/`, `R404a/`, `lp/`, `docs/referencias_tecnicas/` ou materiais de
  scratch, salvo se uma tarefa futura os colocar explicitamente em escopo.
- Antes de alterar arquivos compartilhados (`docs/`, `AGENTS.md`,
  `CLAUDE.md`), sincronizar com `origin/main`.
- Mudanças no site devem passar por lint, build e Preview da Vercel antes da
  integração em `main`.

## Ponto exato para continuar

O site está publicado e funcional, a correção de navegação está em produção e
o modelo de gestão compartilhada já está no GitHub. A próxima sessão deve
começar escolhendo uma das frentes acima, criando uma branch específica e
registrando o responsável principal.
