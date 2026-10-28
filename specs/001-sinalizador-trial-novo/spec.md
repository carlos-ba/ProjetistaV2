# 001 — Sinalizador de trial novo no painel Administração

**Status:** implementado e testado localmente em 2026-10-28 (hipóteses H1–H4 confirmadas pelo responsável) — **não commitado, não publicado**

## Resultado da verificação (2026-10-28)

| Critério | Resultado | Evidência |
|---|---|---|
| A1 cadastro público nasce pendente | ✅ | `test_lead_1` (cadastro real via `/api/auth/register/`) |
| A2 marcar / desfazer | ✅ | `test_lead_2` (inclui UTC explícito) e tela |
| A3 nenhuma empresa existente pendente após a migration | ✅ | banco local: 17 empresas, 0 com campo nulo |
| A4 só trial tem bolinha | ✅ | tela: empresas ativas sem bolinha e sem botão |
| A5 empresa criada pelo superadmin não nasce pendente | ✅ | `test_lead_3` |
| A6 só superadmin marca | ✅ | `test_lead_4` (admin_empresa e membro → 403) |
| A7 marcar não altera assinatura/demais campos | ✅ | `test_lead_5`; `test_lead_6` (editar não trata) |
| A8 tela: bolinha, botão, contador | ✅ | navegador local, conta descartável: vermelho/verde, contador 2→1→2, persistiu após recarregar, abrir Equipe e Editar/Salvar não mudam a cor; sem erro no console |
| A9 migration upgrade→downgrade→upgrade | ✅ | alembic local |
| A10 suíte completa | ✅ | 55/55 (48 + 7 novos); build do frontend ok |

Arquivos: `alembic/versions/0047_empresa_lead_tratado_em.py`, `models/empresa.py`, `api/routes_admin.py`,
`tests/test_admin_lead_trial.py`, `frontend/src/components/AdminEmpresas.jsx`.
Não testado: tela em celular; cadastro trial real em produção (só depois do deploy).
**Data:** 2026-10-28
**Área:** `backend/` + `frontend/` (núcleo do SaaS — Claude)

## Contexto e objetivo

O SaaS já recebe inscrições trial e vendas. Nas vendas o responsável tem o relatório do checkout; nos trials não
tem como saber quais inscrições novas ele já abriu e levou para a planilha/CRM comercial. Objetivo: um **checkpoint
visual de trabalho comercial** na lista de Empresas do painel Administração — bolinha **vermelha** = trial novo
ainda não tratado; **verde** = trial já tratado — que o responsável muda **manualmente**.

É um controle interno do responsável. Não altera a assinatura, não é visto nem afeta o cliente.

## Fatos confirmados (fonte: mensagens do responsável, 2026-10-28)

| # | Fato |
|---|---|
| F1 | Ao se inscrever em trial, aparece no painel Administração um sinalizador (bolinha) **vermelho**: "trial ainda sem os dados abertos/anotados". |
| F2 | O responsável entra no trial, pega o que precisa (telefone etc.), leva para o CRM/planilha e só então o sinalizador vira **verde**. |
| F3 | A mudança de vermelho para verde é **manual** (clique do responsável), nunca automática. |
| F4 | Vale **só daqui para frente**: trials já existentes não geram pendência. |

## Fatos do código (verificados em 2026-10-28)

- Cadastro público cria a empresa em `registrar_usuario` (`backend/app/services/auth.py`) com `status_assinatura="trial"`.
- A lista do painel é `GET /api/v1/admin/empresas` (`routes_admin.py`, só `superadmin_icenexus`), exibida em
  `frontend/src/components/AdminEmpresas.jsx` com o badge de status; a edição é `PATCH /api/v1/admin/empresas/{id}`.
- Telefone e e-mail do trial ficam em `usuario` e já aparecem na "Equipe" expandida de cada empresa.
- Última migration: 0046.

## Hipóteses (assumidas por mim — **confirmar**)

| # | Hipótese | Padrão adotado se não houver objeção |
|---|---|---|
| H1 | O sinalizador só existe para empresas em `status_assinatura = "trial"`. Quando o trial vira `ativa` (venda) ou outro status, a bolinha some (o controle de vendas já vem do checkout). | sim |
| H2 | O responsável pode **desfazer** (voltar de verde para vermelho) caso marque por engano. | sim |
| H3 | Empresas criadas à mão pelo superadmin (implantação) **não** nascem pendentes — não são leads de cadastro público. | sim |
| H4 | Contador de pendentes na aba "Empresas" (ex.: "Empresas • 3") para ver de relance sem rolar a lista. Sugerido na conversa, não confirmado como parte do escopo. | incluído |

## Regras

1. Cada empresa tem um campo `lead_tratado_em` (data/hora, opcional). Vazio = não tratado; preenchido = tratado.
2. Cadastro público de trial grava `lead_tratado_em` **vazio** (nasce pendente). *(F1)*
3. A migration preenche `lead_tratado_em = agora` em **todas as empresas já existentes**, para que nenhuma apareça
   vermelha por causa da mudança. *(F4)*
4. Na lista de Empresas, a bolinha aparece **somente** quando `status_assinatura = "trial"`: vermelha se
   `lead_tratado_em` vazio, verde se preenchido. Demais status: sem bolinha. *(F1, F2, H1)*
5. Há um botão por linha que alterna o estado ("Marcar como tratado" / "Desfazer"), disponível só ao
   `superadmin_icenexus`. A mudança acontece **apenas** por esse clique. *(F3, H2)*
6. Abrir a Equipe, editar a empresa ou qualquer outra ação **não** muda a bolinha. *(F3)*
7. A bolinha não é exposta em nenhuma rota de usuário comum nem em `/me`.

## Critérios de aceite (verificáveis)

| # | Critério | Como verificar |
|---|---|---|
| A1 | Cadastro público novo → empresa trial com `lead_tratado_em` nulo; aparece **vermelha** em `GET /admin/empresas`. | teste de API |
| A2 | `PATCH` de "marcar tratado" grava `lead_tratado_em` e a empresa passa a **verde**; "desfazer" volta a nulo/vermelha. | teste de API |
| A3 | Após a migration, nenhuma empresa existente tem `lead_tratado_em` nulo (nenhuma bolinha vermelha por causa do deploy). | consulta no banco local, antes/depois |
| A4 | Empresa `ativa`/`suspensa`/`cancelada` não exibe bolinha, mesmo com `lead_tratado_em` nulo. | tela + teste |
| A5 | Empresa criada pelo superadmin (`POST /admin/empresas`) não nasce pendente. | teste de API |
| A6 | Usuário que não é superadmin recebe 403 ao tentar marcar/desfazer. | teste de API |
| A7 | Marcar tratado numa empresa não altera `status_assinatura`, `assinatura_fim` nem qualquer outro campo. | teste de API |
| A8 | Na tela: bolinha vermelha/verde na linha, botão alterna sem recarregar a página, contador de pendentes na aba "Empresas" reflete o número de vermelhas e atualiza ao clicar. | verificação no navegador (conta descartável) |
| A9 | Migration `upgrade` → `downgrade` → `upgrade` roda limpa localmente. | alembic local |
| A10 | Suíte completa de testes continua passando (48/48 + novos). | `pytest` |

## Fora de escopo

- Tela/relatório dedicado de "Leads", exportação para CRM, notificação por e-mail/WhatsApp.
- Anotações, histórico de quem/quando tratou (só um carimbo de data/hora).
- Qualquer mudança no que o cliente vê ou no fluxo de assinatura/checkout/trial.
- Bolinha para vendas/assinantes.
- Filtro "só pendentes" na lista (pode virar melhoria depois, se o volume pedir).

## Perguntas abertas

Nenhuma bloqueante. As hipóteses H1–H4 têm padrão definido; basta o responsável dizer se alguma deve mudar.

## Risco de dado de usuário (regra de 2026-09-27)

Migration **aditiva** (coluna nova opcional). O único `UPDATE` é preencher a coluna nova nas empresas existentes;
nenhum dado atual é alterado ou removido. `downgrade` apenas remove a coluna. Sem risco de perda.
