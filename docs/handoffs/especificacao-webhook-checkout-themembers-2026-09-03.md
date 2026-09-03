# Especificação técnica — webhook do Checkout TheMembers para o SaaS IceNexus

**Data:** 2026-09-03

**Origem:** handoff Codex → Claude

**Área responsável pela implementação:** núcleo do SaaS (`backend/` e, quando necessário, `frontend/`)

**Estado:** especificação pronta; nenhuma implementação ou configuração em produção realizada

## 1. Objetivo

Integrar os três produtos pagos do Checkout TheMembers/TheBank ao SaaS IceNexus para que pagamentos e alterações de acesso atualizem automaticamente a empresa (`tenant`) vinculada ao comprador.

Produtos comerciais atuais:

| Oferta | Preço publicado | Link atual de checkout |
|---|---:|---|
| Profissional Mensal | R$ 159/mês | `https://checkout.thebank.com.br/7501283916486672384` |
| Profissional Semestral | 6 × R$ 99 (R$ 594) | `https://checkout.thebank.com.br/7501283403359830016` |
| Premium — Engenharia e Capacitação | 6 × R$ 497 (R$ 2.982) | `https://checkout.thebank.com.br/7501282048323481600` |

A avaliação gratuita continua sendo criada pelo cadastro público atual: 15 dias e 1 projeto.

## 2. Documentação correta e alerta de segurança

O artigo inicialmente avaliado, sobre webhooks da **Área de Membros**, não é o contrato correto para ativação dos planos do SaaS. Ele trata eventos educacionais e usa HMAC-SHA256:

- https://ajuda.themembers.com.br/pt-br/article/como-configurar-webhooks-na-area-de-membros-plataforma-100l7s8/

Para pagamentos deve ser usada a documentação de **Webhooks do Checkout**:

- https://ajuda.themembers.com.br/pt-br/article/webhooks-do-checkout-1adpcv1/

No Checkout, a documentação atual mostra um token estático no cabeçalho `x-signature`. Portanto:

- não aplicar o algoritmo HMAC da Área de Membros neste endpoint;
- validar `x-signature` contra um segredo exclusivo armazenado no Render;
- usar `secrets.compare_digest` para comparação em tempo constante;
- não registrar o token, CPF/CNPJ, telefone completo, cartão ou payload integral em logs comuns.

Se um payload real contradizer a documentação, interromper a ativação e registrar a divergência antes de adaptar o contrato.

## 3. Estado atual do SaaS

O código existente já oferece a base necessária:

- `Empresa.plano`: eixo de produto técnico (`tecnico` ou `empresa`);
- `Empresa.status_assinatura`: `trial`, `ativa`, `suspensa` ou `cancelada`;
- `assinatura_inicio` e `assinatura_fim`;
- cadastro público cria `plano="tecnico"`, `status_assinatura="trial"`, 15 dias;
- e-mail de `Usuario` é único;
- `exigir_pode_editar` preserva leitura/exportação e bloqueia edição quando o trial vence.

### Lacunas que precisam ser corrigidas

1. Não existe rota pública de webhook.
2. Não existe idempotência ou auditoria de eventos do gateway.
3. `Empresa.plano` não diferencia as três ofertas comerciais e **não deve ser reutilizado para isso**, conforme `docs/decisoes/2026-08-30-plano-x-status.md`.
4. `exigir_pode_editar` bloqueia apenas trial vencido. Hoje, gravar `suspensa` ou `cancelada` não bloquearia edição.
5. Um comprador pode pagar usando um e-mail sem conta ou diferente do e-mail cadastrado no SaaS.
6. Os IDs presentes nos links de checkout ainda não foram confirmados como os IDs estáveis recebidos nos payloads.

## 4. Escopo da primeira versão

### Incluído

- receber e autenticar webhooks do Checkout;
- normalizar os dois formatos de envelope documentados;
- garantir idempotência;
- mapear produto para oferta comercial por identificador estável;
- associar comprador a usuário/empresa por e-mail normalizado;
- ativar, renovar, suspender ou cancelar a assinatura;
- guardar compras pendentes quando ainda não existir usuário;
- reconciliar compra pendente depois que o comprador verificar o e-mail da conta;
- registrar auditoria sem expor dados sensíveis;
- testes automatizados de contrato e regras de negócio;
- preservar acesso de leitura/exportação quando a assinatura não permitir edição.

### Fora do escopo

- criação automática de usuário (o checkout não fornece senha/username);
- recuperação de carrinho abandonado;
- emissão de nota fiscal;
- automação do bônus por indicação do Semestral;
- controle de consumo das validações técnicas mensais;
- matrícula automática nos cursos EAD;
- concessão automática dos 70% de desconto presencial;
- alteração de `recursos_avancados_habilitados` sem decisão comercial específica;
- mudanças nas páginas institucionais nesta branch.

## 5. Endpoint

Criar uma rota pública, sem JWT:

```text
POST /api/webhooks/themembers/checkout
```

URL de produção após o deploy:

```text
https://projetista-v2-api-alt.onrender.com/api/webhooks/themembers/checkout
```

### Respostas

| Situação | Resposta |
|---|---|
| Token ausente ou inválido | `401` |
| JSON malformado/contrato impossível de interpretar | `400` ou `422` |
| Evento válido já processado | `200` (idempotente) |
| Evento válido, comprador ainda sem conta | `200`, persistido como pendente |
| Evento válido processado | `200` |
| Falha transitória de banco/processamento | `500`, permitindo retry do provedor |

O processamento inicial é apenas transacional no banco e deve terminar rapidamente. Não chamar APIs externas ou enviar e-mail dentro da resposta do webhook. Caso essas ações sejam acrescentadas, encaminhá-las para processamento assíncrono.

## 6. Configuração e segredos

Adicionar ao `Settings` e a `backend/.env.example`:

```text
THEMEMBERS_WEBHOOK_TOKEN=
THEMEMBERS_PRODUCT_MONTHLY_ID=
THEMEMBERS_PRODUCT_SEMIANNUAL_ID=
THEMEMBERS_PRODUCT_PREMIUM_ID=
```

Regras:

- IDs são `str`, nunca `float`; os valores podem exceder a precisão segura de JavaScript e podem vir como UUID/reference ID;
- não mapear produto por título, valor cobrado ou número de parcelas;
- não commitar valores de token;
- em `APP_ENV=production`, recusar inicialização se a rota estiver habilitada sem token e IDs de produto válidos;
- permitir uma flag explícita `THEMEMBERS_WEBHOOK_ENABLED=false` para deploy seguro antes de cadastrar o webhook no painel.

Os números dos links (`750128...`) são candidatos, não confirmação. Confirmar com um payload real/histórico de cada produto antes de habilitar a automação.

## 7. Modelo de dados

### 7.1. Empresa

Não alterar o significado de `Empresa.plano`. Adicionar um eixo comercial independente:

```text
oferta_comercial: nullable string
```

Valores previstos:

- `avaliacao`
- `profissional_mensal`
- `profissional_semestral`
- `premium`

Migração/backfill:

- empresas com `status_assinatura='trial'` → `oferta_comercial='avaliacao'`;
- contas ativas legadas → manter `NULL` para revisão manual; não inferir plano pago;
- não criar enum rígido no PostgreSQL nesta primeira versão; validar valores na aplicação, seguindo o padrão atual de strings.

### 7.2. Eventos do webhook

Criar tabela de auditoria/idempotência, por exemplo `webhook_checkout_evento`:

```text
id UUID PK
provedor string = "themembers"
chave_evento string UNIQUE NOT NULL
tipo_evento string NOT NULL
objeto string NULL
external_id string NULL
produto_id string NULL
email_comprador_normalizado string NULL
empresa_id UUID NULL FK empresa.id
status_processamento string NOT NULL
erro_resumido string NULL
payload JSONB NOT NULL
recebido_em datetime timezone NOT NULL
processado_em datetime timezone NULL
```

Status sugeridos:

- `recebido`
- `processado`
- `pendente_usuario`
- `produto_desconhecido`
- `ignorado`
- `erro`

O payload contém PII e deve permanecer restrito a banco/admin técnico. Logs de aplicação devem conter apenas `chave_evento`, tipo, produto, estado e identificadores internos.

### 7.3. Referências do gateway

Adicionar campos mínimos à empresa ou, preferencialmente, uma tabela separada de vínculo atual da assinatura:

```text
provedor
external_customer_id
external_product_id
external_order_id
external_subscription_code
status_gateway
proxima_cobranca_em
ultimo_pagamento_em
```

Recomendação: tabela separada (`assinatura_gateway`) para preservar histórico e permitir troca de oferta. `Empresa.status_assinatura`, `oferta_comercial`, `assinatura_inicio` e `assinatura_fim` permanecem como projeção rápida usada pelo produto.

## 8. Normalização do payload

A documentação apresenta ao menos dois formatos:

### Envelope com `payload`

```json
{
  "company": {},
  "payload": {
    "id": "...",
    "object": "order",
    "event": "release.access",
    "data": {}
  }
}
```

### Evento direto

```json
{
  "object": "transaction",
  "event": "transaction.approved",
  "created_at": "...",
  "data": {}
}
```

Normalizador:

1. Se `body.payload` for objeto e contiver `event`, usar `body.payload` como envelope lógico.
2. Caso contrário, usar o próprio `body`.
3. Extrair `event`, `object`, `external_id`, comprador, produto, pedido, assinatura e datas por funções específicas e testadas.
4. Campos documentados como opcionais ou `null` não podem quebrar o endpoint.

## 9. Idempotência

Construir `chave_evento` nesta ordem:

1. identificador explícito do evento, quando presente;
2. `event + payload.id`;
3. `event + data.id`;
4. fallback: `event + SHA-256` do corpo recebido.

Inserir a chave sob constraint única antes de aplicar efeitos. Corrida entre duas entregas deve resultar em uma única mutação. Evento duplicado já concluído retorna `200`.

Se a primeira tentativa terminou em `erro`, permitir replay controlado pelo serviço/admin; não reexecutar cegamente sem conhecer o ponto de falha.

## 10. Associação do comprador

Extrair o e-mail, por ordem, de estruturas como:

- `data.customer.email`;
- `data.subscription.subscriber.email`;
- `data.order.customer.email`.

Normalizar com `strip().lower()` e localizar por comparação case-insensitive em `Usuario.email`.

### Conta existente

- encontrar o usuário único;
- aplicar o efeito na `Empresa` vinculada;
- guardar `empresa_id` no evento.

### Conta inexistente

- não criar usuário automaticamente;
- persistir como `pendente_usuario` e retornar `200`;
- após verificação do e-mail (`verificar_email`), reconciliar eventos pendentes do mesmo e-mail;
- se mais de um evento conflitante estiver pendente, processar cronologicamente e terminar no estado mais recente.

Recomendação comercial para as páginas/checkouts, depois que a integração estiver pronta:

> Para ativação automática, utilize no pagamento o mesmo e-mail cadastrado na IceNexus.

## 11. Mapeamento dos eventos

| Evento | Efeito no SaaS |
|---|---|
| `release.access` | Autoridade principal para ativar. Mapear produto, gravar oferta, `status_assinatura='ativa'`, início e término disponíveis no payload. |
| `revoke.access` | Autoridade principal para remover acesso de escrita. Gravar `status_assinatura='cancelada'` e data correspondente. |
| `transaction.approved` | Registrar pagamento/renovação. Atualizar último pagamento, assinatura, próxima cobrança e término. Pode ativar como fallback somente se o produto estiver inequivocamente mapeado. |
| `transaction.refunded` | `status_assinatura='cancelada'`; bloquear escrita imediatamente. |
| `transaction.charged_back` | `status_assinatura='suspensa'`; bloquear escrita imediatamente e sinalizar para revisão. |
| `transaction.failed` | Registrar tentativa; não bloquear imediatamente, pois podem existir retentativas ou período já pago. |
| `transaction.pending_refund` | Registrar; não alterar acesso até confirmação. |
| `order.completed` | Auditoria; não duplicar ativação se `release.access`/`transaction.approved` já foram processados. |
| `order.canceled` / `order.expired` | Auditoria de compra inicial; não cancelar conta ativa sem correlação inequívoca com a assinatura atual. |
| `abandoned` | Fora do escopo inicial. |

### Precedência

- `refunded`/`charged_back`/`revoke.access` prevalecem sobre aprovação anterior da mesma compra/assinatura;
- eventos antigos não podem reativar estado cancelado por evento mais recente;
- comparar timestamps do provedor e preservar o último evento aplicado por vínculo de assinatura.

## 12. Datas e duração

- Mensal: usar `subscription.next_billing_at`/período recebido após cada pagamento aprovado.
- Semestral e Premium: usar `product.expires_in` quando enviado por `release.access`.
- Se a TheMembers não enviar término para Semestral/Premium, calcular seis meses a partir do pagamento somente após confirmar essa regra com payload real.
- Não usar “180 dias” silenciosamente se o contrato comercial pretende seis meses de calendário.
- Datas do provedor devem ser interpretadas com timezone e persistidas em UTC; converter para `date` apenas na projeção atual da empresa.
- Contas legadas `ativa` com `assinatura_fim=NULL` continuam válidas até revisão manual.

## 13. Regra de bloqueio

Atualizar `exigir_pode_editar` para bloquear quando:

1. trial venceu;
2. `status_assinatura` for `suspensa` ou `cancelada`;
3. assinatura ativa tiver `assinatura_fim` definida e já encerrada.

Leitura e exportação devem continuar liberadas, conforme a decisão atual do produto.

Mensagens sugeridas:

- trial: mensagem já existente;
- suspensa: “Sua assinatura está suspensa. Regularize o pagamento para voltar a editar.”;
- cancelada/expirada: “Sua assinatura não está ativa. Assine um plano para voltar a editar.”

## 14. Direitos por oferta

Na primeira versão, `oferta_comercial` identifica a oferta e permite exibição/administração, mas não deve inventar direitos ainda não implementados:

- Mensal e Semestral: mesma plataforma completa; diferença comercial de cobrança/duração;
- Premium: plataforma + serviços de engenharia/capacitação descritos na oferta;
- não automatizar quantidade mensal de validações sem módulo próprio;
- não ligar `recursos_avancados_habilitados` automaticamente, pois essa relação comercial ainda não foi decidida;
- bônus por indicação do Semestral permanece operação manual até existir regra formal.

## 15. Estrutura sugerida de código

Sem prescrever nomes rígidos, separar responsabilidades:

```text
backend/app/api/routes_webhooks_themembers.py
backend/app/schemas/webhook_themembers.py
backend/app/services/webhook_themembers.py
backend/app/models/webhook_checkout_evento.py
backend/app/models/assinatura_gateway.py
backend/alembic/versions/00xx_webhook_checkout_themembers.py
```

O router deve apenas autenticar, ler/validar o JSON e chamar o serviço. Regras de ativação, reconciliação, idempotência e mapeamento ficam no serviço, reutilizáveis por replay administrativo.

## 16. Testes obrigatórios

1. rejeita token ausente;
2. rejeita token incorreto;
3. aceita token correto;
4. normaliza envelope direto e envelope dentro de `payload`;
5. `release.access` ativa empresa existente;
6. produto mensal/semestral/Premium mapeia para oferta correta;
7. produto desconhecido não ativa e fica sinalizado;
8. evento duplicado retorna `200` sem repetir mutação;
9. corrida de duplicados é contida pela constraint única;
10. e-mail é associado sem diferença de maiúsculas/minúsculas;
11. comprador sem conta fica pendente;
12. verificação posterior do e-mail reconcilia pendência;
13. `revoke.access`, refund e chargeback bloqueiam escrita;
14. `transaction.failed` não bloqueia acesso já pago;
15. evento cronologicamente antigo não reativa assinatura cancelada por evento novo;
16. IDs numéricos grandes são preservados como string;
17. campos opcionais `null` não derrubam o endpoint;
18. trial vencido continua bloqueado;
19. conta ativa expirada passa a bloquear;
20. conta legada ativa com fim `NULL` permanece utilizável;
21. falha de banco retorna `500` e não marca evento como processado;
22. logs não contêm token, CPF/CNPJ, telefone, cartão ou payload integral.

Usar fixtures sanitizadas baseadas nos payloads oficiais e, depois, acrescentar fixtures sanitizadas dos três payloads reais capturados no histórico da TheMembers.

## 17. Observabilidade e operação

- log estruturado: chave do evento, tipo, produto, empresa encontrada, resultado e duração;
- métrica/alerta para `produto_desconhecido`, `pendente_usuario` e `erro`;
- consulta administrativa ou script para listar pendências e reprocessar um evento específico;
- nunca oferecer replay em massa sem filtro;
- registrar o payload original no banco para auditoria, com acesso restrito.

## 18. Sequência segura de implantação

1. Criar branch própria a partir da `main` mais recente. Não usar a branch das páginas.
2. Implementar modelos, migration, endpoint, serviço e testes.
3. Rodar suíte local e revisar migration/downgrade.
4. Adicionar as variáveis no Render com webhook desabilitado.
5. Fazer deploy do endpoint.
6. Confirmar que token ausente/incorreto retorna `401`, sem alterar dados.
7. No painel TheMembers: **Checkout → Ferramentas → Webhooks → + Novo Webhook**.
8. Nome sugerido: `IceNexus SaaS — Produção`.
9. Cadastrar a URL do endpoint e selecionar somente os três produtos.
10. Selecionar inicialmente: `release.access`, `revoke.access`, `transaction.approved`, `transaction.refunded`, `transaction.charged_back`, `transaction.failed`, `transaction.pending_refund`.
11. Usar o mesmo token forte cadastrado no Render.
12. Realizar transação controlada com uma conta IceNexus e o mesmo e-mail.
13. Consultar o histórico do webhook e salvar payload sanitizado de cada tipo de produto.
14. Confirmar IDs reais, datas e comportamento de cancelamento/renovação.
15. Atualizar as variáveis de produto se necessário e habilitar o processamento.
16. Testar renovação/cancelamento ou simulação suportada pela plataforma antes de considerar concluído.
17. Só então publicar a orientação de “mesmo e-mail” e liberar os checkouts no site oficial.

## 19. Critérios de aceite

- pagamento aprovado de cada um dos três produtos ativa a empresa correta;
- ativação aparece em `/api/auth/me/` após novo login/refresh de dados;
- avaliação vencida volta a permitir edição após ativação;
- cancelamento/refund/chargeback bloqueia escrita sem apagar projetos;
- renovação mensal atualiza a próxima validade sem duplicar registros;
- evento repetido não altera datas/estado novamente;
- compra sem conta não é perdida e é conciliada após verificação do mesmo e-mail;
- produto desconhecido nunca concede acesso;
- endpoint rejeita assinatura inválida;
- nenhum segredo ou PII aparece nos logs;
- painel administrativo permite ao menos diagnosticar eventos pendentes/erro;
- documentação de deploy e `.env.example` são atualizadas.

## 20. Pendências que exigem confirmação real

Antes de finalizar o mapeamento, obter no histórico do webhook:

1. payload de `release.access` ou `transaction.approved` do Mensal;
2. payload do Semestral;
3. payload do Premium;
4. IDs estáveis de produto/reference;
5. comportamento do mensal em renovação e falha de cobrança;
6. momento exato em que `revoke.access` é emitido;
7. presença e semântica de `expires_in` nos três produtos;
8. se Semestral/Premium são produtos avulsos com seis parcelas ou assinaturas recorrentes;
9. se os eventos de acesso são emitidos para esses produtos sem configuração adicional de plataforma.

Não resolver essas pendências por suposição baseada apenas no título, preço ou URL do checkout.
