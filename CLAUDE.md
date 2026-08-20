# CLAUDE.md — ProjetistaV2

Leia este arquivo no início de toda sessão. Ele descreve o estado real do projeto,
como rodar localmente, convenções adotadas e o que está pendente de implementar.

---

## Checklist de início de sessão (rodar 1x, só em sessão nova)

Antes de iniciar qualquer tarefa em uma sessão nova (não repetir a cada mensagem
nem em continuações da mesma sessão), rode em paralelo:

```bash
ls backend/alembic/versions/ | sort | tail -3
git log -1 --format="%ad %s" --date=short
```

- Se a migration mais recente for **maior** que a última listada na tabela
  "Banco de Dados — Migrations" abaixo, ou a data do commit for **posterior** à
  data em "Estado atual do código" — este arquivo está desatualizado.
- Avise o usuário em 1-2 frases (não faça auditoria completa sozinho) e pergunte
  se deve atualizar o CLAUDE.md antes de seguir. Isso evita acumular divergência
  como a que foi corrigida em 2026-08-10 (arquivo estava 5 migrations e 6 semanas
  atrasado).

---

## Identidade do Produto

**IceNexus** — SaaS de dimensionamento frigorífico para técnicos e engenheiros de refrigeração.
Substitui planilhas manuais por um wizard guiado de 6 etapas.

**Não confundir com "IceNexus IAR"** — nome reservado para uma plataforma diferente e
futura, ainda não desenvolvida (ver projeto `icenexusiar-ai-lab`, já existente no
Vercel/Render, ainda não explorado). Documentos comerciais antigos
(`docs/comercial/IceNexus_IAR_*.pdf`, já enviados a um prospect real) mantêm o nome
antigo por serem registro histórico — não foram reemitidos.

---

## Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI + SQLAlchemy 2.0 async + PostgreSQL + Alembic |
| Driver DB | psycopg3 (`psycopg[binary]`) — string: `postgresql+psycopg://` |
| Frontend | React 19 + Vite + Tailwind CSS + shadcn/ui |
| Deploy backend | Render (auto-deploy no push para `main`) |
| Deploy frontend | Vercel (auto-deploy no push para `main`) |
| Migrations | Alembic (0001→0026), roda no `startCommand` do Render |

---

## Ambiente Local (PC2 — notebook)

### Subir o backend

```powershell
cd C:\projetos\ProjetistaV2\backend
C:\projetos\ProjetistaV2\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

### Subir o frontend

```powershell
cd C:\projetos\ProjetistaV2\frontend
npm run dev
```

Frontend abre em `http://localhost:5173`. Backend em `http://localhost:8000`.

### Banco local

- PostgreSQL 17 na porta 5432
- Database: `projetista_v2`, User: `projetista`
- Conectar: `$env:PGPASSWORD = "projetista"; & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U projetista -p 5432 -d projetista_v2`

### Variáveis de ambiente (.env no backend/)

```
DATABASE_URL=postgresql+psycopg://projetista:projetista@localhost:5432/projetista_v2
SECRET_KEY=...
```

---

## URLs de Produção

| Serviço | URL |
|---------|-----|
| Frontend | https://projetista-v2.vercel.app |
| Backend API | https://projetista-v2-api-alt.onrender.com |
| API Docs | https://projetista-v2-api-alt.onrender.com/docs |
| GitHub | https://github.com/carlos-ba/ProjetistaV2 |

---

## Estrutura do Wizard (6 Cards)

O fluxo é um wizard linear. Cada card passa dados para o próximo via callbacks em `App.jsx`.

| Card | Componente | Descrição |
|------|-----------|-----------|
| 1 | `CalculadoraGabinete.jsx` | Dimensões, isolamento (painel PIR Kingspan), temperatura interna, tipo de piso, portas frigoríficas |
| 2 | `CalculadoraCargaTermica.jsx` | Cálculo de carga térmica (kcal/h) |
| 3 | `SelecaoEquipamentos.jsx` | Seleção de UC + Evaporadora do banco de dados |
| 4 | `CalculadoraTubulacao.jsx` | Dimensionamento de tubulação (bitolas ASHRAE) + isolamento Armacel |
| 5 | `ComponentesFluxo.jsx` | Componentes de fluxo: solenoide, filtro, visor, separadores, tanque, cavalete, carga fluido |
| 6 | `GeradorOrcamento.jsx` | Geração de orçamento + Lista de Engenharia (Excel/PDF) + cotação Excel + proposta comercial PDF |

**Atenção:** o Card 5 (ComponentesFluxo) é o mais complexo — leia a seção abaixo com atenção.

---

## Card 5 — ComponentesFluxo — Estado Atual (completo)

### Dois modos de seleção

**Modo Automático** (padrão) — todos os itens implementados:

| Componente | Endpoint | Observação |
|-----------|----------|-----------|
| Separador de Líquido | `POST /api/v1/componentes` | banco de dados |
| Separador de Óleo | `POST /api/v1/componentes` | banco de dados |
| Válvula Solenoide | `POST /api/v1/solenoide/selecionar` | motor Kv interno (R404A/R22) |
| Filtro Secador (DML/DMC) | `POST /api/v1/acessorios/selecionar` | DML com tanque / DMC sem tanque |
| Visor de Líquido (SGN) | `POST /api/v1/acessorios/selecionar` | pelo diâmetro da linha de líquido |
| Tanque de Líquido | `POST /api/v1/tanque-liquido/selecionar` | NBR 16.069 (Castel, RAC) |
| Carga de Fluido | `POST /api/v1/carga-fluido/estimar` | kg por trecho (evap + linhas) |
| Cavalete (luvas/porcas/reduções) | `POST /api/v1/cavalete/analisar` | análise automática de conexões |

As buscas rodam em paralelo via `Promise.allSettled`. O tanque de líquido e o cavalete são encadeados após a estimativa de carga de fluido.

**Modo Engenharia**:
- Abre CoolSelector®2 Online (Danfoss) para seleção manual
- Mostra parâmetros do projeto (fluido, T.Evap, T.Cond, capacidade em kW)
- Técnico registra manualmente VET, Filtro Secador, Solenoide, Visor de Líquido
- Separadores ainda vêm do banco automaticamente

### Motor de seleção de solenoide

- Arquivo: `backend/app/services/solenoide.py`
- Endpoint: `POST /api/v1/solenoide/selecionar`
- Parâmetros: `fluido`, `te_c`, `tc_c`, `capacidade_kw`, `dp_bar` (default 0.10)
- Fluidos suportados: **R404A** e **R22** (tabelas do CoolPack/DTU)
- Fórmula: `Q[kW] = Kv × √(1000 × ΔP × ρ_L) × Δh / 3600`
- Família: Danfoss EVR v2 (EVR2 a EVR40), ordenados por Kv crescente
- Margem de segurança: 10% (seleciona menor EVR com Q_válvula ≥ Q_requerida × 1.10)
- Validado contra CoolSelector2 local: EVR 6 man v2 para R404A -25°C/-35°C 5.8kW ✓

### Filtro Secador (Danfoss)

- Arquivo: `backend/app/services/acessorios.py`
- Regra DML vs DMC:
  - **DML** = sistema com tanque de líquido separado (padrão refrigeração comercial)
  - **DMC** = sistema pequeno SEM tanque de líquido (combinado receptor + filtro)
  - **DCL** = igual ao DML mas com 20% alumina ativada — R22 com óleo mineral, T.Cond alta
- Seleção pelo diâmetro da linha de líquido (informado pelo Card 4 — tubulação)
- Toggle `tem_tanque_liquido` (bool) define DML ou DMC

### Visor de Líquido (Danfoss SGN)

- Arquivo: `backend/app/services/acessorios.py`
- Seleção exclusivamente pelo diâmetro da linha de líquido
- Tamanhos: SGN 6 (1/4"), SGN 10 (3/8"), SGN 12 (1/2"), SGN 16 (5/8"), SGN 19 (3/4"), SGN 22s (7/8")

---

## Convenções de Nomenclatura (OBRIGATÓRIO seguir)

| Termo correto | Não usar |
|---------------|----------|
| **tanque de líquido** | receptor, receiver |
| **T. Evaporação / T.Evap** | temperatura de evaporação (abrev.) |
| **T. Condensação / T.Cond** | — |
| **T. Ambiente / T.Amb** | temperatura externa |
| **kcal/h** | BTU/h (não usado neste projeto) |
| **kW** | unidade usada no CoolSelector e nos cálculos internos |

---

## Multi-tenancy (Fase A — em produção desde 2026-08-05)

Tenant = **empresa**. Toda conta pertence a uma `empresa` (nome, plano, status de
assinatura). Papéis: `superadmin_icenexus` (equipe IceNexus) | `admin_empresa` |
`membro`.

- `empresa_id` escopa: `projeto`, `cliente`, `fornecedor`, `cotacao`,
  `proposta_comercial`, `configuracao_montagem`. `owner_id` continua existindo
  como autor (auditoria), mas o filtro de acesso é sempre por `empresa_id`.
- Dependência `get_empresa_atual` (`backend/app/services/auth.py`) retorna 403
  se o usuário não tiver empresa vinculada.
- Catálogo técnico (equipamento/material/componente) continua **global**, sem
  dono, só especificação — preço e código interno por empresa é a **Fase B**
  (ver seção própria abaixo), em produção desde 2026-08-20.
- Painel admin: `frontend/src/components/AdminEmpresas.jsx` + rotas
  `/api/v1/admin/*` (só `superadmin_icenexus`).
- Scripts operacionais em `backend/scripts/`: `promover_superadmin.py`,
  `copiar_projetos.py`, `remover_contas.py`, `backfill_empresa.py` — todos
  simulam por padrão, só gravam com `--aplicar`.

Detalhes de implantação, armadilhas técnicas (MissingGreenlet, `--reload`
travando) e o passo manual obrigatório pós-deploy (`promover_superadmin.py`)
estão na memória — ver `project-fase-a-multitenancy` e
`project-multitenancy-assinatura`.

---

## Limite de Sessões + Logout Real (em produção desde 2026-08-19)

Anti-compartilhamento de conta: máximo de **2 sessões simultâneas** por usuário
(fixo no código, ainda não configurável por empresa). Estourar o limite bloqueia
o login novo com aviso explícito — não derruba a sessão antiga em silêncio.

- Tabela `sessao_usuario` (migration 0025): uma linha por sessão ativa; claim
  `sid` embutido no access e no refresh token é o elo entre o token e a linha.
- `POST /api/auth/logout/` revoga a sessão de verdade no servidor — antes o
  "Sair" só limpava o `localStorage` e o token continuava válido até expirar.
- **Liberação remota de sessão (2026-08-20):** fechar a aba sem logout não expira
  nada (refresh token dura 30 dias) — sessão "fantasma" travava login em outro
  dispositivo. O 403 de limite agora devolve a lista de sessões ativas (dispositivo/
  IP/último uso) e `POST /api/auth/token/encerrar-sessao/` (reautentica com
  usuário+senha) encerra uma delas e completa o login — sem precisar acessar o
  dispositivo antigo. UI em `LoginPage.jsx`. Detalhe em `project-design-limite-sessoes`.
- Métrica de sessões ativas + IPs distintos/24h visível pro admin (`AdminEmpresas.jsx`)
  — só visibilidade, não bloqueia nada automaticamente (IP é sinal ruidoso).
- Retenção de 90 dias (LGPD) — limpeza via
  `backend/scripts/limpar_sessoes_antigas.py`, manual (sem cron no projeto).

Detalhe completo, decisões e testes: ver `project-design-limite-sessoes` na memória.

---

## Fase B — Catálogo e Lista de Preços por Empresa (em produção desde 2026-08-20)

Cada empresa pode ter sua própria lista de preços (tabela `produto_empresa`,
migration 0026), usada no orçamento **em vez** do catálogo técnico global — que
agora é só especificação, sem preço (`Material.custo`/`Equipamento.custo` saíram
da cascata de `gerar_orcamento`).

- **Casamento por descrição normalizada** (`app/core/matching.py`, `norm()` —
  extraído de `casar_itens()` em `cotacao_import.py`), não por id. Nem todo item
  do orçamento carrega um id estável de catálogo (painéis, portas, materiais
  extras do gabinete não têm `ref_id`).
- **Cascata de preço** (`obter_mapa_precos()` em
  `backend/app/services/produto_empresa.py`): lista da própria empresa → senão o
  último preço de cotação confirmado daquele item, qualquer projeto (consulta ao
  vivo em `cotacao_item`, sem tabela nem job de sincronização) → sem preço.
  Resolvida no **frontend** (`GeradorOrcamento.jsx` busca
  `GET /api/v1/produto-empresa/mapa-precos` e mescla no `precoMap` que já existe
  pra cotação — nunca sobrescreve o preço de uma cotação escolhida pra este
  projeto). `POST /api/v1/orcamento` continua sem autenticação, de propósito.
- **Dois perfis de cliente, mesma tabela, população diferente** (decisão de
  produto): loja/revenda cadastra via **implantação paga** (superadmin, painel
  "📦 Catálogo" em `AdminEmpresas.jsx`, por empresa); montadora não cadastra nada
  — a cascata de cotação histórica resolve sozinha.
- **Autoadministração:** `admin_empresa`/`superadmin_icenexus` editam a própria
  lista sem precisar acionar o superadmin — item "Catálogo de Preços" no menu
  lateral (`CatalogoPrecosPage.jsx`), rotas `/api/v1/produto-empresa/*`
  (`get_empresa_atual`). Implantação cross-tenant fica em
  `/api/v1/admin/empresas/{id}/produtos/*` (só `superadmin_icenexus`).
- Componente de lista/CRUD (`CatalogoPrecosEmpresa.jsx`) é compartilhado entre os
  dois contextos — só muda o `apiBase` recebido.
- Fora de escopo por decisão: produtos de parceiro (fora do catálogo global, sem
  `ref_global`) e busca assistida no catálogo pela UI — ficam pra depois.

Detalhe completo do design e do refinamento: ver `project-multitenancy-assinatura`
na memória, e `DESIGN_MULTITENANCY_ASSINATURA_2026-07-28.md` (seção 4.3).

---

## Banco de Dados — Migrations (0001→0026)

| Migration | Conteúdo |
|-----------|---------|
| 0001 | Schema completo v2 (todas as tabelas base) |
| 0002 | Verificação de e-mail no usuário |
| 0003 | Campo `consumo_kw` em performance de equipamento |
| 0004 | Campo `temp_ambiente` em performance de equipamento |
| 0005 | Tabela `painel_frigorifico` (Kingspan Isoeste PIR) |
| 0006 | Tabela `isolamento_tubulacao` |
| 0007 | Tabela `porta_frigoriifica` |
| 0008 | Tabela `cotacao` com fornecedor |
| 0009 | Tabela `proposta` comercial PDF |
| 0010 | Campo `volume_conexoes` em equipamento |
| 0011 | Conexões em condensadoras |
| 0012 | Tabela `configuracao_montagem` (perfis de montagem) |
| 0013 | Flags em `configuracao_montagem` |
| 0014 | Tabela `cliente` |
| 0015 | Tabela `peso_tubo_cobre` |
| 0016 | Campo `qtde_metros` em cotacao_item |
| 0017 | Classificação de orçamento (`bloco_orcamento`, `classificacao_item`, `item_classificacao`) |
| 0018 | Correção da VET para R404A |
| 0019 | Campo `modo_engenharia` em usuário |
| 0020 | Multi-tenancy: tabela `empresa`, `usuario.empresa_id` + `papel` (nullable) |
| 0021 | Backfill de `empresa_id` + NOT NULL + FK RESTRICT |
| 0022 | Nome de projeto único por empresa (desambigua duplicatas existentes antes de criar a constraint) |
| 0023 | Classificação "Válvulas de Bloqueio (GBC)" (`valvula_bloqueio_gbc`) |
| 0024 | Tabela `embalagem_fluido` (embalagem descartável por fluido, seed de teste só R404A) |
| 0025 | Tabela `sessao_usuario` (limite de sessões simultâneas + logout real + métrica de IP) |
| 0026 | Tabela `produto_empresa` (Fase B — lista de preços/catálogo privado por empresa) |

---

## Endpoints Backend (25 arquivos de rota em `backend/app/api/`)

| Endpoint | Método | Função |
|----------|--------|--------|
| `/api/auth/*` | POST/GET | Autenticação JWT + sessão (limite 2 simultâneas, `/logout/` revoga no servidor) — nota: sem `/v1` |
| `/api/v1/admin/*` | GET/PATCH | Empresas + usuários — só `superadmin_icenexus` |
| `/api/v1/projetos` | GET/POST/PATCH | CRUD projetos + `dados_completos` (JSON) |
| `/api/v1/clientes` | GET/POST | Gestão de clientes |
| `/api/v1/catalogo/paineis/fabricantes` | GET | Painéis PIR Kingspan |
| `/api/v1/catalogo/portas` | GET | Portas frigoríficas |
| `/api/v1/gabinete` | POST | Cálculo câmara: lista_corte + materiais |
| `/api/v1/carga-termica` | POST | Cálculo kcal/h (Card 2) |
| `/api/v1/selecao` | POST | Busca UC + Evaporadora (Card 3) |
| `/api/v1/tubulacao` | POST | Dimensionamento ASHRAE (Card 4) |
| `/api/v1/componentes` | POST | Separadores do banco (Card 5) |
| `/api/v1/solenoide/selecionar` | POST | Seleção EVR v2 por Kv (Card 5) |
| `/api/v1/acessorios/selecionar` | POST | Filtro DML/DMC + Visor SGN (Card 5) |
| `/api/v1/carga-fluido/estimar` | POST | Estimativa carga fluido em kg (Card 5) |
| `/api/v1/tanque-liquido/selecionar` | POST | Tanque vertical NBR 16.069 (Card 5) |
| `/api/v1/cavalete/analisar` | POST | Luvas, porcas, reduções + válvulas de bloqueio GBC (Card 5) |
| `/api/v1/embalagem-fluido` | GET | Catálogo de embalagens de fluido por fluido (Card 6) |
| `/api/v1/orcamento` | POST | Consolidação orçamento (Card 6) — sem auth, de propósito |
| `/api/v1/produto-empresa/*` | GET/POST/PATCH/DELETE | Lista de preços — autoadministração (Fase B) |
| `/api/v1/classificacoes` | GET/POST | Árvore de classificação (blocos/tipos) |
| `/api/v1/cotacoes/*` | GET/POST/PATCH | Geração/importação planilha Excel |
| `/api/v1/propostas/*` | GET/POST | Proposta comercial PDF |
| `/api/v1/configuracoes/*` | GET/POST | Perfis de montagem (tipo filtro, visor, trechos) |
| `/api/seed/*` | POST | Seed de dados (dev/setup) |
| `/health` ou `/api/v1/health` | GET | Health check |

---

## Catálogo carregado no App com retry

O catálogo (fabricantes de painel, portas) é carregado **no `App.jsx`** antes de renderizar qualquer card, com retry automático a cada 2s até sucesso. **Nunca buscar catálogo dentro de um componente filho.** Passar sempre via props.

---

## Fluxo de Projetos — Salvar/Carregar

- Projetos salvos via `PATCH /api/v1/projetos/{id}` com campo `dados_completos` (JSON contendo estado de todos os cards)
- Carregamento automático ao abrir o projeto — reconstrói o estado de cada card
- **Invalidação em cascata:** se Card 1 recalcula → Cards 2-6 marcados como `invalidados`. Se Card 2 recalcula → Cards 3-6 invalidados. E assim por diante.

---

## Fluxo de Cotação e Proposta (implementado)

- **Fase 1:** Geração de planilha Excel de cotação com lista de materiais e equipamentos (colunas metros + kg para tubos de cobre)
- **Fase 2:** Importação da planilha devolvida pelo fornecedor com preços preenchidos
- **Fase 3:** Geração de proposta comercial em PDF com preços da cotação
- Acessível via sidebar "Cotações" (`PainelCotacoes.jsx`) e `GeradorOrcamento.jsx`

---

## Fluxo de Trabalho Obrigatório (SEGUIR SEMPRE)

```
EDITAR LOCAL → TESTAR LOCAL → COMMIT → PUSH → PRODUÇÃO
```

**NUNCA editar diretamente em produção. NUNCA fazer push sem testar local primeiro.**

### Passo a passo

1. **Editar** os arquivos em `C:\projetos\ProjetistaV2\`
2. **Subir o backend local** (nova aba do terminal):
   ```powershell
   cd C:\projetos\ProjetistaV2\backend
   C:\projetos\ProjetistaV2\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
   ```
3. **Subir o frontend local** (nova aba do terminal):
   ```powershell
   cd C:\projetos\ProjetistaV2\frontend
   npm run dev
   ```
4. **Testar** em `http://localhost:5173` — verificar TODOS os pontos alterados
5. **Confirmar** com o usuário que está tudo ok
6. **Commit** com mensagem descritiva:
   ```powershell
   cd C:\projetos\ProjetistaV2
   git add backend/... frontend/...
   git commit -m "fix: descrição do que foi corrigido"
   ```
7. **Push** para produção (Render + Vercel auto-deploy):
   ```powershell
   git push origin main
   ```

### Regras derivadas

- Acumular mudanças relacionadas no mesmo commit — não fazer um push por arquivo
- Jamais usar `--no-verify` para pular verificações
- Se o teste local falhar, corrigir antes de qualquer push
- `--reload` só no backend local; produção usa o comando do Render sem `--reload`

---

## Regras de Desenvolvimento

1. **Fluidos suportados no motor de solenoide:** R404A e R22. Para outros, redirecionar ao CoolSelector
2. **T.Condensação calculada como:** T.Amb + 10°C (padrão de mercado brasileiro)
3. **Catálogo de componentes no banco:** separadores de líquido e óleo vêm do banco via `/api/v1/componentes`. VET, filtro secador, solenoide e visor são calculados/selecionados pelo próprio sistema
4. **Catálogo global × catálogo da empresa:** o catálogo técnico (equipamentos, componentes) é global e gerenciado pelo admin SaaS, só especificação, sem preço. Preços e códigos internos por empresa ficam em `produto_empresa` — **Fase B** (ver seção própria acima)
5. **Campo `temp_condensacao` no banco** armazena T.Amb conforme publicado nos catálogos dos fabricantes brasileiros. T.Cond real = T.Amb + ΔT (nunca assumir fixo)

---

## Catálogo Técnico

Painéis, unidades condensadoras e evaporadoras vêm de múltiplos fabricantes
(Elgin, Danfoss Optyma, Mipal, Isoeste/MBP). Novo fornecedor = preencher um dos
templates na raiz (`template_paineis_frigorificos.xlsx`,
`template_unidades_condensadoras.xlsx`, `template_evaporadoras.xlsx`) e rodar o
importador correspondente em `backend/scripts/` (`importar_paineis.py`,
`importar_equipamentos.py`) — upsert idempotente por chave única, nunca duplica.
Rodar local primeiro, depois em produção com `DATABASE_URL` do Render na env
(nunca colar a credencial no chat).

Classificação de itens do orçamento é via banco (`bloco_orcamento`,
`classificacao_item`, `item_classificacao`), servida por `GET
/api/v1/classificacoes`. Todos os geradores (gabinete, tubulação, cavalete,
componentes, equipamentos, portas) emitem `tipo_item` (slug estável) — **não
existe mais classificação por string-matching no frontend**. Editável sem
deploy pela página "Classificação de Itens" no menu lateral.

Rate-limiting da API foi adiado de propósito para pré-lançamento (ver
`project-auditoria-20260708` na memória).

---

## Estado atual do código (auditado em 2026-08-20)

| Funcionalidade | Status |
|---------------|--------|
| Wizard 6 cards | ✅ funcional |
| Autenticação JWT | ✅ |
| Gabinete + painéis PIR Kingspan + portas | ✅ |
| Carga térmica | ✅ |
| Seleção UC + Evaporadora | ✅ |
| Tubulação ASHRAE + isolamento Armacel | ✅ |
| Card 5 — Separadores (banco de dados) | ✅ |
| Card 5 — Solenoide automático (R404A/R22) | ✅ motor Kv |
| Card 5 — Filtro secador automático (DML/DMC) | ✅ |
| Card 5 — Visor de líquido automático (SGN) | ✅ |
| Card 5 — Tanque de Líquido (NBR 16.069) | ✅ |
| Card 5 — Carga de Fluido (kg por trecho) | ✅ |
| Card 5 — Cavalete (luvas/porcas/reduções + válvulas GBC) | ✅ |
| Card 5 — Modo Engenharia (CoolSelector) | ✅ |
| Card 6 — Embalagem de fluido (Card 6, converte kg em cilindros) | ✅ só R404A tem dado real |
| Insight de estimativa de capacidade (coluna esquerda) | ✅ informativo, nunca usado em cálculo |
| Orçamento + Cotação Excel + Proposta PDF | ✅ |
| Verificação de cotação antes de gerar proposta | ✅ funcional, ajustes pendentes |
| Proposta com preços da cotação (via preco_unitario) | ✅ |
| Modal resumo ao carregar projeto | ✅ |
| Aviso "pode estar desatualizado" nos cards | ✅ |
| Salvar/Carregar projeto (dados_completos) | ✅ |
| Configurações de montagem (perfis) | ✅ |
| Gestão de clientes | ✅ |
| Diagrama SVG do cavalete (flutuante) | ✅ |
| Multi-tenancy — empresa/papéis/isolamento (Fase A) | ✅ em produção desde 2026-08-05 |
| Limite de sessões + logout real + métrica IP (admin) | ✅ em produção desde 2026-08-19 |
| Lista de Engenharia exportável (Excel/PDF) — Card 6 | ✅ em produção desde 2026-08-19 |
| Catálogo/lista de preços por empresa (Fase B) | ✅ em produção desde 2026-08-20 |
| Multiusuário/convites + painel admin ampliado (Fase C) | ❌ |
| Billing real / gateway (Fase D) | ❌ |
| IA com Tool Use | ❌ |

---

## Fluxo de Verificação de Cotação — Card 6

### Lógica ao clicar "💰 GERAR PROPOSTA AO CLIENTE"

1. Busca `GET /api/v1/cotacoes?projeto_id={id}` filtrando status ≠ `cancelada`
2. **Nenhuma cotação** → aviso âmbar + botões para gerar planilha ou abrir painel de cotações
3. **Cotação(ões) mas nenhuma `processada`** → aviso azul com código(s) + botão para abrir painel
4. **1 cotação `processada`** → gera direto com os preços dela
5. **2+ cotações `processadas`** → modal de escolha: uma específica OU "Melhor preço por item" (min entre todas)

### Injeção de preços

- O frontend busca `GET /api/v1/cotacoes/{id}` para cada cotação selecionada
- Constrói um `precoMap: Map<norm(descricao), preco>` (casamento por descrição normalizada, igual ao `casar_itens()` do backend)
- Mescla o mapa de preços da empresa (`GET /api/v1/produto-empresa/mapa-precos`, Fase B) por cima — só preenche o que a cotação deste projeto não cobriu, nunca sobrescreve
- Injeta `preco_unitario` em cada item do payload do orçamento
- O backend (`backend/app/schemas/orcamento.py`) aceita `preco_unitario: float | None` em `ItemOrcamento`
- O serviço (`backend/app/services/orcamento.py`) usa esse valor se presente; sem fallback pro catálogo global (Fase B — ver seção própria)

### Itens sem preço

- Itens não encontrados na cotação ficam com `preco_unitario=null` → backend retorna `custo_unitario_rs=0`
- Após gerar, aparece seção âmbar com lista dos itens sem preço + inputs para preço manual
- Botão "Recalcular" regenera a proposta usando `ultimoPrecoMapRef` (preços da cotação) + preços manuais como override

### Riscos conhecidos

- O casamento por descrição pode falhar se a descrição gerada no orçamento diferir da descrição gravada na cotação (ex: complementos livres, itens do gabinete com área no detalhe)
- Fluxo de gestão de cotações ainda simples — módulo dedicado planejado para uma fase futura

Histórico de implementação e pendências já resolvidas: ver `project-cotacao-verificacao` na memória.

---

## Disciplina de Contexto e Custo (trabalhar comigo)

O `CLAUDE.md` e o índice de memória são recarregados **inteiros a cada mensagem**
da sessão — por isso ficam enxutos. O que infla o custo de verdade é o que se
acumula durante a conversa: arquivos lidos, screenshots, saída de comandos. Uma
sessão que mistura 5 assuntos carrega o peso de todos eles em cada mensagem, até
a última.

Regras práticas:

1. **Uma sessão por frente de trabalho.** Ao mudar de assunto (ex: terminou o
   catálogo, vai começar a Fase B), abrir sessão nova em vez de continuar na
   mesma.
2. **Ritual de encerramento**, antes de trocar de assunto ou fechar por hoje:
   pedir para registrar na memória o que foi decidido/pendente e, se mudou algo
   estrutural (endpoint, migration, fluxo), atualizar este arquivo — depois
   `/clear`. Isso é compactação controlada, melhor que deixar a automática
   decidir o que descartar no meio de uma tarefa.
3. **`/compact` com instrução explícita** (ex: "preserve os arquivos alterados e
   as pendências, descarte saídas de comando") quando ainda falta trabalho no
   mesmo assunto e o contexto já passou de ~50%.
4. **Pedir trecho, não arquivo inteiro**, quando o arquivo é grande — "lê a
   função X em `arquivo.py`" custa uma fração de "lê o `arquivo.py`".
5. **Extrair PDF/imagem uma vez, trabalhar sobre o texto** — não repassar página
   por página como imagem.
6. **Modelo por tarefa:** Sonnet para tarefas mecânicas (rodar script, conferir
   migration, ajustar texto); Opus para arquitetura e depuração difícil.
