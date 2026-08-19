# Design — Limite de sessões simultâneas, logout real e monitoramento de IP

**Data:** 2026-08-16 · **Status:** implementado, testado e em produção desde 2026-08-19
(commits `12db5a1` backend, `590de60` frontend; migration `0025_sessao_usuario`).
Discussão sem código, documentado antes de mexer no banco/backend.

---

## 1. Contexto e motivação

Preocupação: um usuário pode emprestar/compartilhar a senha da conta com mais de uma pessoa,
gerando múltiplos acessos simultâneos sob a mesma licença sem que o sistema perceba ou reaja.

Objetivo: mitigar isso sem punir uso legítimo (um técnico em desktop + celular, por exemplo) e
sem depender de um sinal ruidoso (IP) para bloquear — só para dar visibilidade ao admin.

---

## 2. Auditoria do estado atual (2026-08-16)

**Autenticação é JWT puro, sem estado.** `POST /api/auth/token/` (`autenticar_usuario`,
`backend/app/services/auth.py`) verifica usuário/senha e emite um par `access`/`refresh` novo — sem
checar nem invalidar nada emitido antes. Tecnicamente, a mesma senha pode gerar qualquer número de
sessões simultâneas, sem nenhum atrito.

**Não existe nenhum rastreamento de sessão.** Os tokens carregam só `sub` (id do usuário), `type`
(`access`/`refresh`) e `exp` (`backend/app/core/security.py`). Nenhum `jti`, nenhuma tabela de
sessões, nenhum campo de "último login" no `usuario`.

**Logout é cosmético.** `logout()` no frontend (`frontend/src/contexts/AuthContext.jsx:57-61`) só
apaga `access_token`/`refresh_token` do `localStorage` — nunca chama o backend. O access token
continua criptograficamente válido até expirar sozinho (`ACCESS_TOKEN_EXPIRE_MINUTES`), mesmo depois
do usuário clicar em "Sair". Não existe endpoint de logout no backend.

**Conclusão da auditoria:** zero proteção hoje contra compartilhamento de conta, e o "logout" não
encerra nada de fato do lado do servidor.

---

## 3. Decisões tomadas (usuário, 2026-08-16)

Entre as opções levantadas (sessão única / limite de sessões / monitoramento de IP sem bloqueio /
resolver via convite multiusuário — Fase C, ainda não construída), o usuário escolheu combinar:

1. **Limite de sessões simultâneas** (não sessão única) — tolera uso legítimo em mais de um
   dispositivo, sem exigir que o fluxo de convite de segunda pessoa (Fase C) exista antes.
2. **Logout deve encerrar a sessão de verdade no servidor** — hoje não encerra (ver auditoria acima).
3. **Monitorar IPs distintos por usuário/dia como métrica no painel do admin — sem bloquear
   automaticamente.** Serve de subsídio para o admin investigar, não como trava.

As três pedem, na prática, a mesma peça de infraestrutura: uma tabela de sessões.

---

## 4. Arquitetura-alvo

### 4.1 Tabela nova — `sessao_usuario`

Uma linha por sessão ativa. Login cria; logout, expiração ou estouro do limite revoga.

| Coluna | Tipo | Nulo? | Papel |
|---|---|---|---|
| `id` | UUID (PK) | não | Identificador da sessão. Vai embutido como claim `sid` no access **e** no refresh token — é o elo entre "token que o navegador carrega" e "linha que o banco controla". |
| `usuario_id` | UUID (FK → `usuario`, `ondelete=CASCADE`) | não | Dono da sessão. Indexado — coluna mais consultada (contar sessões ativas no login, listar sessões de um usuário no admin). |
| `ip` | String(45) | sim | IP capturado no momento do login (45 cobre IPv6). Base da métrica de IPs distintos/dia. |
| `user_agent` | String(255) | sim | Navegador/dispositivo capturado no login — ajuda o admin a diferenciar dispositivos numa lista. |
| `ultimo_uso_em` | timestamp | não | Atualizado quando o refresh token da sessão é usado (não a cada requisição — evitar gravação no banco em toda chamada). Decide qual sessão está "mais parada" na hora de liberar vaga do limite. |
| `revogada_em` | timestamp | sim | `NULL` = sessão viva. Preenchido no logout explícito, ao estourar o limite (a mais parada é revogada pra abrir vaga), ou se o admin derrubar alguém manualmente no futuro. |
| `created_at` | timestamp | não | Herdado do `TimestampMixin` padrão do projeto — momento do login. |

### 4.2 Mudanças de mecanismo (sem código ainda, só o desenho)

- `create_access_token`/`create_refresh_token` ganham um claim a mais: `sid`, com o `id` da linha de
  `sessao_usuario` criada no login.
- `get_current_user` (dependência usada em toda rota autenticada), além de validar a assinatura do
  JWT, passa a checar se a sessão `sid` existe e `revogada_em IS NULL`. É isso que torna o logout
  real — hoje o servidor nunca sabe que alguém saiu.
- **No login:** conta sessões não revogadas do `usuario_id`; se atingir o limite, revoga a de
  `ultimo_uso_em` mais antigo antes de criar a nova.
- **No logout:** revoga a linha da sessão atual (endpoint novo, hoje não existe).
- **No refresh:** além de emitir novo access token, atualiza `ultimo_uso_em` da sessão.

### 4.3 Métrica de IPs distintos (admin)

Consulta simples em cima da mesma tabela, sem estrutura extra:

```sql
SELECT usuario_id, date_trunc('day', created_at) AS dia, count(DISTINCT ip) AS ips_distintos
FROM sessao_usuario
GROUP BY usuario_id, dia
```

Exibida como métrica no painel do admin (`AdminEmpresas.jsx` ou equivalente) — não bloqueia nada
automaticamente, só dá subsídio para investigação manual.

**Ressalva registrada:** IP bruto é um sinal ruidoso para este produto — técnico de campo troca de
local o dia inteiro e 4G/5G já roda vários IPs sozinho por handoff de torre. 3-4 IPs distintos no
mesmo dia pode ser um dia normal de trabalho, não compartilhamento. Começar com contagem bruta (o
que foi pedido); se virar ruído demais na prática, evoluir para geolocalização (cidade/estado por
IP) como sinal mais informativo — não é bloqueante para a primeira versão.

---

## 5. Decisões (fechadas em 2026-08-19)

1. **Número do limite de sessões: 2.**
2. **Comportamento ao estourar o limite: bloquear o login novo com aviso explícito** (ex: "Limite de
   sessões atingido — saia de outro dispositivo primeiro"). Não derruba a sessão mais antiga em
   silêncio — o usuário precisa agir.
3. **Retenção de `sessao_usuario`: janela de 60-90 dias.** Sessões revogadas/expiradas mais antigas
   que isso podem ser limpas (mecanismo de limpeza a definir na implementação — provavelmente script
   manual em `backend/scripts/`, seguindo o padrão dos demais scripts do projeto, já que não há
   infraestrutura de cron hoje).
4. **Limite fixo no código por enquanto**, não configurável por empresa/plano — a Fase B (planos por
   empresa) ainda não existe, então não há um conceito de "plano" pra atrelar o limite ainda. Pode
   virar configurável quando a Fase B chegar.

**Confirmado explicitamente fora de escopo:** fechar o navegador/aba sem clicar em "Sair" continua
sem exigir novo login — sessão guardada em `localStorage` (persistente), como já era antes deste
design. Esse comportamento não muda com a implementação abaixo.

---

## 6. Não implementado

Nada deste desenho foi codado ainda — nem migration, nem mudança em `security.py`/`auth.py`/
`AuthContext.jsx`. Este documento existe para registrar a decisão antes de mexer em autenticação
(área sensível) e permitir revisão antes de qualquer commit de código.
