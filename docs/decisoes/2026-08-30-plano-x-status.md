# Plano × Status — dois eixos independentes na assinatura

**Data:** 2026-08-30
**Decisão:** `plano` (produto contratado) e `status_assinatura` (estado
atual da assinatura) são eixos **independentes**. `plano` nunca vale
"trial" — "trial" existe exclusivamente em `status_assinatura`.

## Antes (confuso e arriscado)

- `plano`: `trial` | `tecnico` | `empresa`
- `status_assinatura`: `trial` | `ativa` | `suspensa` | `cancelada`

"Trial" existia nos dois campos, quase se sobrepondo. Isso permitia
combinações incoerentes (ex: admin promove o `plano` pra `tecnico` mas
esquece de tirar o `status` de `trial`) que, dependendo de como a trava de
edição era escrita, podiam travar por engano a edição de um cliente
**pagante** quando a validade antiga do trial vencesse — bug real,
corrigido no commit `4cb5b98` amarrando a trava aos dois campos como
paliativo antes desta decisão.

## Depois (modelo adotado)

- **`plano`** (`tecnico` | `empresa`) — só o produto contratado. Todo
  cadastro já nasce com um plano real definido: self-serve
  (`/api/auth/register/`) sempre `tecnico`; `empresa` só existe via
  implantação assistida pelo admin (nunca muda depois, é o mesmo produto
  do início ao fim do relacionamento).
- **`status_assinatura`** (`trial` | `ativa` | `suspensa` | `cancelada`) —
  o estado atual da cobrança, para qualquer plano. "Trial" é a fase
  temporária de avaliação (com `assinatura_fim`) que qualquer produto tem
  antes do pagamento ser confirmado.

Confirmar pagamento = trocar só o `status` pra `ativa`. O `plano` nunca
muda nesse momento — já estava certo desde o cadastro.

## Por que isso é melhor

- Elimina a combinação incoerente pela raiz — `plano='trial'` deixa de
  existir, então não tem como um cliente pagante ficar travado por um
  `status` esquecido.
- `Empresa.trial_expirado` simplifica: volta a checar só
  `status_assinatura=='trial'` (não precisa mais checar os dois campos).
- Generaliza o mecanismo de trial pra qualquer plano — se um dia a
  IceNexus quiser oferecer trial pro plano `empresa` (ex: prospect de
  revenda testando antes de fechar), o mecanismo já funciona sem mudança
  de código: é só `status='trial'` com `assinatura_fim`, `plano` já pode
  ser `empresa` desde o início.

## Implementação (commit em `main`, mesma data)

- `backend/app/models/empresa.py`: `plano` default vira `"tecnico"`
  (era `"trial"`); `trial_expirado` volta a checar só `status_assinatura`.
- `backend/app/services/auth.py`: `registrar_usuario` grava
  `plano="tecnico"` (era `"trial"`).
- `backend/app/services/assinatura.py`: `exigir_limite_projetos_trial`
  passa a checar `status_assinatura != "trial"` (era `plano != "trial"`).
- `frontend/src/components/AdminEmpresas.jsx`: "Trial" removido da lista
  de `PLANOS`; legenda no formulário de edição reescrita.
- `backend/scripts/backfill_plano_tecnico.py`: backfill idempotente —
  toda empresa com `plano='trial'` (só existe via cadastro self-serve
  antigo, é sempre e só `tecnico` de verdade) vira `plano='tecnico'`.
  Rodado local (6 empresas) — **produção pendente**, rodar depois do
  deploy do código.

## Pendência

Rodar `backfill_plano_tecnico.py --aplicar` contra produção
(`DATABASE_URL` do Render na env local, nunca colar credencial no chat).
