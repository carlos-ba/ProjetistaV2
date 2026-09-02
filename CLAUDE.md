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

## Gestão Compartilhada Multi-Agente (Codex + Claude)

Desde 2026-08-25, o ecossistema IceNexus é desenvolvido em gestão compartilhada
entre dois agentes de IA: Codex (`site-ecosistema/` — comercial, conteúdo,
UI/UX institucional) e Claude (`backend/`, `frontend/` — núcleo do SaaS). O
GitHub é a fonte única de verdade. `AGENTS.md` orienta o Codex; ambos apontam
para a mesma documentação central em `docs/`. Regra central: uma tarefa → uma
branch → um responsável principal — nunca editar os mesmos arquivos em
paralelo pelos dois agentes. Modelo completo, divisão de responsabilidade e
fluxo de revisão cruzada: ver `docs/decisoes/2026-08-25-gestao-compartilhada-multiagente.md`.

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
| Site institucional | Next.js em `site-ecosistema/`, Vercel próprio (Root Directory `site-ecosistema`, auto-deploy no push para `main`) |
| Migrations | Alembic (0001→0029), roda no `startCommand` do Render |

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
| Frontend (app) | https://camara-fria.icenexus.com.br (domínio real; `https://projetista-v2.vercel.app` é o deploy Vercel por trás, ainda no ar) |
| Backend API | https://projetista-v2-api-alt.onrender.com |
| API Docs | https://projetista-v2-api-alt.onrender.com/docs |
| GitHub | https://github.com/carlos-ba/ProjetistaV2 |
| Site institucional | https://icenexus.com.br (hub do ecossistema + `/projeto-camara-fria` com planos/preços) — código em `site-ecosistema/` neste repo desde 2026-08-24, Next.js, deploy Vercel próprio (`icenexus-site`) |

---

## Estrutura do Wizard (6 Cards)

O fluxo é um wizard linear. Cada card passa dados para o próximo via callbacks em `App.jsx`.

| Card | Componente | Descrição |
|------|-----------|-----------|
| 1 | `CalculadoraGabinete.jsx` | Dimensões, isolamento (painel PIR Kingspan), temperatura interna, tipo de piso, portas frigoríficas, kit de montagem (perfis/selante/rebite/parafuso) |
| 2 | `CalculadoraCargaTermica.jsx` | Cálculo de carga térmica (kcal/h) |
| 3 | `SelecaoEquipamentos.jsx` | Seleção de UC + Evaporadora do banco de dados |
| 4 | `CalculadoraTubulacao.jsx` | Dimensionamento de tubulação (bitolas ASHRAE) + isolamento Armacel |
| 5 | `ComponentesFluxo.jsx` | Componentes de fluxo: solenoide, filtro, visor, separadores, tanque, cavalete, carga fluido |
| 6 | `GeradorOrcamento.jsx` | Geração de orçamento + Lista de Engenharia (Excel/PDF) + cotação Excel + proposta comercial PDF |

**Atenção:** o Card 5 (ComponentesFluxo) é o mais complexo — leia a seção abaixo com atenção.

---

## Card 1 — Kit de Montagem (perfis, selante, rebite, parafuso+bucha)

Em produção desde 2026-09-01. Arquivos: `backend/app/services/kit_montagem.py`
(seleção + cálculo), `backend/app/services/calculos_gabinete.py` (geometria),
`backend/app/models/kit_montagem.py`, `backend/app/models/perfil_metalico.py`.
Design completo: `DESIGN_KIT_MONTAGEM_2026-09-01.md`.

Substitui a antiga linha única "Acessórios de Montagem (Kit)" (placeholder em
m², sem cálculo real) por uma lista de itens de verdade, resolvida dentro de
`POST /api/v1/gabinete`.

- **Fica no Card 1, não no Card 5** — mesmo dependendo do banco (como os do
  Card 5), a geometria que usa (perímetro do teto/piso, altura da parede,
  espessura do painel) já é calculada dentro de `calcular_gabinete()`; não tem
  nenhuma dependência do domínio de refrigeração (fluido, T.Evap etc).
  `calculos_gabinete.py` continua síncrono/sem DB — o kit é resolvido à parte
  em `kit_montagem.py`, chamado pela rota, que junta os dois resultados.
- **Seleção automática cobre 3 dos 5 tipos de perfil** (Ângulo Externo, Ângulo
  Interno, U) — Liso, Z, e qualquer variação fora do padrão de 40mm (aba
  configurável em `ConfiguracaoMontagem.largura_aba_padrao_mm`) só entram via
  seleção manual no próprio Card 1 (catálogo servido por
  `GET /api/v1/catalogo/perfis-metalicos`).
- **Fallback de medida:** quando a espessura do painel não bate exato com
  nenhuma medida cadastrada, pega o próximo tamanho **acima** (nunca abaixo) e
  sinaliza no `detalhe` do item ("sem medida exata... usado Xmm").
- **`avisos_kit_montagem`** na resposta do `/api/v1/gabinete`: quando não
  existe nenhum perfil compatível no catálogo (ou selante/rebite/parafuso não
  cadastrados), o item simplesmente não entra na lista — sem esse campo,
  sumia em silêncio, sem indicar ao técnico que faltou cadastro. Renderizado
  como banner vermelho no Card 1, acima da tabela de materiais.
- **Selante de PU:** metros lineares de todos os perfis (auto + manual, em
  barras já arredondadas pra cima) × 2, mais área de painéis × 0,145 — tudo
  ÷ rendimento (`ConfiguracaoMontagem.rendimento_selante_m_por_embalagem`),
  com fator de segurança editável no próprio Card 1 (campo independente da
  margem de segurança do Card 2).
- **Rebite:** metros lineares totais × 1000 ÷ 200, × 2 (duas linhas por perfil).
- **Parafuso+Bucha:** só no Perfil U (piso) — metros lineares × 1000 ÷ 500
  (uma linha só).
- **Selante/Rebite/Parafuso+Bucha são catálogos pequenos de propósito**
  (cadastro simples: fabricante + código + descrição, ~1 linha cada, sem
  seleção por especificação) — decisão consciente de não construir
  importador nem tela de admin pra isso (desproporcional ao volume de dado).
  Cadastro novo/atualização = migration com `bulk_insert`, mesmo padrão já
  usado pra `embalagem_fluido` (0024).
- **Classificação:** os `tipo_item` novos (`perfil_angulo_externo`,
  `perfil_angulo_interno`, `perfil_u`, `perfil_manual`, `selante_montagem`,
  `rebite`, `parafuso_bucha`) entram na mesma classificação "Acessórios de
  Montagem" (id=5) que a linha antiga já usava — seed direto na migration
  0028, sem precisar cadastrar manualmente na página "Classificação de Itens".
- **Catálogo real em produção desde 2026-09-01** (migration 0029): 91 perfis
  MBP Isoblock + Selante/Rebite/Parafuso+Bucha com fabricante "Genérico" (sem
  fornecedor específico definido ainda).

---

## Card 1 — Barreira de Vapor (piso convencional)

Em produção desde 2026-09-02. Arquivos: `backend/app/services/barreira_vapor.py`
(cálculo + busca no catálogo), `backend/app/models/catalogo_generico.py`.
Design completo: ver memória `project-pendencia-desmembrar-barreira-vapor`.

Substitui a antiga linha única "Barreira de Vapor" (placeholder em m², sem
composição real) por 3 itens reais, resolvidos dentro de `POST /api/v1/gabinete`
junto com o kit de montagem (mesma condição — só quando `tipo_piso == "convencional"`).

- **Fórmulas confirmadas com quem elaborou a planilha de referência (VALFIM)**,
  validadas contra um projeto real de 134 m² de área de piso:
  - Lona Val Film: área do piso × 1,20 → m²
  - Fita Branca: `ceil((área × 1,20 / 223) × 1,50)` → rolos (223 = rendimento
    m²/rolo, 1,50 = fator de segurança — ambos fixos no código por decisão
    consciente; viram campo configurável em `configuracao_montagem` se um dia
    precisarem variar por projeto, mesmo caminho já percorrido pelo
    `rendimento_selante_m_por_embalagem` do kit de montagem)
  - Lona: (área do piso × 1,32) / 4 → m
- **`catalogo_generico` é uma tabela nova, compartilhada por `tipo_item`**
  (`lona_val_film`, `fita_branca`, `lona`, busca sempre
  `WHERE tipo_item=... AND ativo ORDER BY id LIMIT 1`) — decisão consciente de
  não abrir mais uma tabela dedicada por item (como `selante_montagem`/
  `rebite`/`parafuso_bucha`, migration 0028, que continuam como estão) depois
  de ver o mesmo formato se repetir uma 2ª vez. Colunas: `tipo_item`,
  `fabricante_id` (sempre preenchido — usa o fabricante "Genérico", id 14,
  quando não há fornecedor específico, em vez de aceitar nulo), `codigo_fabricante`,
  `descricao`, `tipo_embalagem` (opcional, só informativo), `observacao`
  (texto livre), `ativo` (soft-delete). É o molde pra próxima leva de cadastro
  simples que aparecer — não só pra barreira de vapor.
- **Avisos reaproveitam `avisos_kit_montagem`** na resposta do `/api/v1/gabinete`
  (mesmo campo, mesmo banner vermelho no Card 1) em vez de um campo novo — item
  sem cadastro no catálogo some da lista e aparece no aviso, mesma mecânica do
  kit de montagem.
- `area_piso_m2` exposto em `GabineteResponse` (0.0 quando o piso não é
  "convencional") pra alimentar esse cálculo sem duplicar geometria — mesmo
  padrão de `area_total_paineis_m2`/`comp_parede_m` já usado pelo kit de montagem.

---

## Card 1 — Concreto Armado (piso convencional) — nota informativa, não é material

Em produção desde 2026-09-02. Decisão combinada com o usuário em 2026-08-17
(`DESIGN_OPCIONAIS_CAMARA_2026-08-17.md`), implementada nesta data.

- **Não é mais `MaterialExtra`** — concreto é obra civil (outra equipe/
  fornecedor), não peça de refrigeração; misturar no mesmo orçamento de
  peças e componentes é erro de categoria, não só UX. Antes entrava
  automaticamente na lista de materiais do Card 1 **e pré-selecionado** no
  checklist do Card 6 (todo item nasce com o checkbox marcado por padrão) —
  o técnico precisava lembrar de desmarcar toda vez.
- `GabineteResponse.volume_concreto_m3` (0.0 quando não há concreto) expõe
  só o volume calculado — mesmo padrão de `area_piso_m2`/`comp_parede_m`,
  sem duplicar geometria. Renderizado no Card 1 como nota informativa (faixa
  azul, não vermelha — não é aviso de erro): "valide o volume com o
  responsável pela obra".
- **Sem retroatividade** — projetos já salvos com "Concreto Armado" no
  orçamento continuam exibindo normalmente; a classificação `concreto_armado`
  (`item_classificacao`) não foi removida do banco, só parou de ser gerada
  pra cálculo novo.
- Placas de Isolamento e os 3 itens de Barreira de Vapor continuam como
  itens normais de orçamento — só o concreto saiu.

---

## Card 3 — Seleção de Equipamentos (interpolação bilinear)

Em produção desde 2026-08-31. Arquivo: `backend/app/services/selecao_equipamentos.py`.

- **T.Ambiente é variável mandatária** — vem do Card 1 (`temperatura_ambiente`),
  propagada por toda a jornada (Card 1 → 2 → 3 → 5). T.Condensação é sempre
  derivada (`T.Amb + 10°C`), nunca um input independente.
- Seleção de UC/Evaporadora interpola em **dois eixos**: agrupa
  `PerformanceEquipamento` por T.Ambiente cadastrada, bracketa a T.Ambiente do
  projeto entre dois grupos, interpola em T.Evaporação dentro de cada grupo
  (lógica 1D que já existia), depois interpola os dois resultados entre si no
  eixo T.Ambiente.
- **Clamp no piso, sem extrapolar no teto:** T.Ambiente do projeto abaixo do
  menor ponto cadastrado usa esse piso direto (seguro — capacidade real a
  T.Ambiente menor tende a ser maior, nunca superdimensiona). Acima do maior
  ponto cadastrado continua sem resultado — extrapolar pra cima seria otimista.
- **Categoria/fluido com um único ponto de T.Ambiente cadastrado** (toda a
  Evaporadora hoje — capacidade real não depende de T.Ambiente, só de
  T.Evaporação, e o cadastro tem um valor-placeholder fixo em 32°C) pula o
  bracket de T.Ambiente inteiramente, interpola só em T.Evaporação. Sem essa
  regra, qualquer projeto com T.Ambiente ≠ 32° exatos zerava a busca de
  Evaporadora.
- Piso do catálogo hoje: **32°C** pra todo fluido/categoria de Unidade
  Condensadora — dado real dos fabricantes (Danfoss/Elgin não publicam tabela
  abaixo disso), não lacuna de cadastro.

---

## Card 5 — ComponentesFluxo — Estado Atual (completo)

### Dois modos de seleção

**Modo Automático** (padrão) — todos os itens implementados:

| Componente | Endpoint | Observação |
|-----------|----------|-----------|
| Separador de Líquido | `POST /api/v1/componentes` | banco de dados |
| Separador de Óleo | `POST /api/v1/componentes` | banco de dados |
| Válvula de Expansão Termostática (VET) | `POST /api/v1/componentes` | banco de dados; corpo Danfoss T2 fixo, modelo cadastrado como `"T2 - N"` (N = 0 a 6, ou X = menor orifício da linha) |
| Válvula Solenoide | `POST /api/v1/solenoide/selecionar` | motor Kv interno (R404A/R22) |
| Filtro Secador (DML/DMC) | `POST /api/v1/acessorios/selecionar` | DML com tanque / DMC sem tanque |
| Visor de Líquido (SGN) | `POST /api/v1/acessorios/selecionar` | pelo diâmetro da linha de líquido |
| Tanque de Líquido | `POST /api/v1/tanque-liquido/selecionar` | NBR 16.069 (Castel, RAC) |
| Carga de Fluido | `POST /api/v1/carga-fluido/estimar` | kg por trecho (evap + linhas) |
| Cavalete (luvas/porcas/reduções) | `POST /api/v1/cavalete/analisar` | análise automática de conexões |

As buscas rodam em paralelo via `Promise.allSettled`. O tanque de líquido e o cavalete são encadeados após a estimativa de carga de fluido.

**Desmembramento em 2 itens na lista (em produção desde 2026-08-31):** VET e
Válvula Solenoide são compradas como peças separadas na prática, mesmo o
Card 5 selecionando/mostrando um conjunto só. O desmembramento acontece só na
hora de montar a lista (orçamento automático e lista de engenharia manual),
via helper compartilhado `desmembrarItem()` em `ComponentesFluxo.jsx`:
- VET: `modelo.split(' - ')` → **"Corpo Válvula de Expansão {corpo}"** +
  **"Orifício de Expansão {orifício}"** (split direto da string já cadastrada,
  sem dado novo).
- Solenoide: **"Válvula Solenoide {modelo}"** + **"Bobina Válvula Solenoide"**
  (genérica, sem tensão — modelagem de tensão por bobina fica pra uma revisão
  futura, decisão consciente pra não atrasar o lançamento).

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

## Card 2 — Cálculo de Carga Térmica

Em produção desde 2026-08-31. Arquivo: `frontend/src/components/CalculadoraCargaTermica.jsx`.

Todos os parâmetros de `CargaTermicaRequest` que o backend já aceitava como
opcionais viraram campos editáveis na UI (antes vinham hardcoded no payload,
apesar do schema já suportar qualquer valor): horas de iluminação/dia, horas
de ocupação/dia, horas de outros motores/dia e margem de segurança (%).

- **Detecção de "dados modificados"** (badge + botão âmbar quando o cálculo
  fica desatualizado) usa uma lista de dependências **separada** do snapshot
  de persistência (`onValoresChange`) — são dois `useEffect` distintos. Ao
  adicionar um campo editável novo neste card, atualizar as **duas** listas,
  não só a de persistência (foi o bug corrigido em 2026-08-31: mudar a margem
  de segurança não acendia o aviso).

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
  simulam por padrão, só gravam com `--aplicar`. `buscar_usuario.py` (só
  leitura, sem `--aplicar`) consulta usuário por username/e-mail parcial —
  status da conta, empresa, sessões ativas. `buscar_projeto.py` (só leitura)
  consulta projeto por nome parcial — imprime gabinete, inputs de carga
  térmica e `dados_completos` já calculado, sem a imagem base64.

Detalhes de implantação, armadilhas técnicas (MissingGreenlet, `--reload`
travando) e o passo manual obrigatório pós-deploy (`promover_superadmin.py`)
estão na memória — ver `project-fase-a-multitenancy` e
`project-multitenancy-assinatura`.

---

## Recursos Avançados por Empresa (em produção desde 2026-09-02)

`Empresa.recursos_avancados_habilitados` (boolean, default `false`) controla
a visibilidade de **"Classificação de Itens"** e **"Catálogo de Preços"** no
menu lateral — nascem desligados pra toda empresa (Técnico ou Empresa,
mesmo campo pros dois planos), o `superadmin_icenexus` liga por exceção no
painel Administração (checkbox no formulário de editar empresa).

- **Decisão consciente: só esconde no frontend, sem gate no backend.** As
  rotas de leitura que esses dois recursos também servem
  (`GET /api/v1/classificacoes`, `GET /api/v1/produto-empresa/mapa-precos`)
  são usadas pelo Card 6 de **qualquer** usuário pra rotular itens e buscar
  preço no orçamento — travar ali quebraria o fluxo normal do wizard. Só as
  rotas de **edição** desses catálogos ficariam sob o flag se um dia o
  bloqueio no backend for adicionado; hoje não há enforcement nenhum lá,
  por pedido explícito do usuário (área sensível, minimizar risco).
- Exposto em `/me` via `Usuario.empresa_recursos_avancados_habilitados`
  (property, mesmo padrão de `empresa_trial_expirado`) →
  `UserOut.empresa_recursos_avancados_habilitados`.

---

## Captura de Lead — Telefone/WhatsApp no Cadastro (em produção desde 2026-09-02)

`usuario.telefone` — obrigatório só no cadastro público (`POST /api/auth/register/`,
jornada trial self-serve), nunca no login. Coluna nullable no banco (contas
antigas não têm, e usuário adicional criado pelo admin dentro de uma
empresa existente também não é obrigado — não é lead, é membro de cliente
que já converteu).

- Validação (`UserCreate.telefone`, `backend/app/schemas/auth.py`): aceita
  com ou sem máscara, normaliza pra só dígitos, exige DDD + número (10 ou
  11 dígitos) — sem verificação por SMS, decisão consciente pra não
  complicar o cadastro nesta fase.
- Exposto em `UsuarioAdminOut` → aparece na "Equipe" de cada empresa no
  painel Administração, como link direto pro WhatsApp
  (`https://wa.me/55{telefone}`) ao lado do e-mail — clica e abre a
  conversa, sem copiar/colar número.
- Fora de escopo por decisão consciente: tela dedicada de "Leads" (lista
  filtrada/ordenada por data de trial) — não compensa pro volume atual;
  revisar se o volume de trial crescer e virar rotina de consulta diária.

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

## Trial de 15 Dias — Trava Real (em produção desde 2026-08-25)

Cadastro novo (`registrar_usuario`) grava `plano="tecnico"` +
`status_assinatura="trial"` + `assinatura_inicio`/`assinatura_fim` (hoje +
15 dias) — antes gravava `plano="trial"` + `status_assinatura="ativa"` sem
prazo, e o trial nunca expirava.

**`plano` (técnico/empresa) e `status_assinatura` (trial/ativa/suspensa/
cancelada) são eixos independentes — `plano` nunca vale "trial"** (decisão
2026-08-30, ver `docs/decisoes/2026-08-30-plano-x-status.md`). "Trial" é
só uma fase temporária de qualquer produto, não um produto em si; confirmar
pagamento troca `status_assinatura` pra `"ativa"`, nunca o `plano`.

- `Empresa.trial_expirado` (`backend/app/models/empresa.py`) — true só
  quando `status_assinatura=='trial'` E `assinatura_fim` já passou.
  `assinatura_fim IS NULL` nunca expira (protege empresas criadas antes
  desta mudança, todas sem essa data preenchida).
- `backend/app/services/assinatura.py`: `exigir_pode_editar` (dependency
  usada em `POST`/`PATCH /api/v1/projetos` — bloqueia com 403 quando o
  trial venceu; `GET` continua liberado, então visualizar e exportar
  PDF/Excel nunca trava) + `exigir_limite_projetos_trial` (bloqueia criar o
  2º projeto quando `status_assinatura=='trial'`, para qualquer plano).
- `UserOut`/`Usuario` expõem `empresa_assinatura_fim` (date) e
  `empresa_trial_expirado` (bool) — o frontend lê o boolean pronto, não
  recalcula data.
- Frontend (`App.jsx`): aviso de assinatura com três ramos explícitos
  (suspensa / cancelada / trial — antes um `!== 'ativa'` genérico conflava
  os três, o que quebraria a UI de todo trial novo). Trial mostra contagem
  regressiva real; vencido, mostra aviso vermelho e desabilita
  "Salvar"/"Salvar Como".
- **Trava de edição nos Cards 1-5 (em produção desde 2026-08-31):** o backend
  só bloqueia `POST`/`PATCH /api/v1/projetos` — todo o resto (cálculos de
  cada card, geração de orçamento, export Excel/PDF) roda sem nenhuma
  checagem de trial, de propósito. Sem trava no frontend também, um trial
  vencido conseguia editar/recalcular os 6 cards livremente e até exportar
  Lista de Engenharia com dados nunca salvos — só não conseguia clicar em
  "Salvar" (achado testando em produção). Fix em `EtapaCard.jsx` (prop
  `bloqueadoTrial`) + `App.jsx`: esconde "Editar" e impede o card renderizar
  expandido nos Cards 1-5 quando o trial venceu (cadeado no lugar). Card 6
  (Orçamento/Lista de Engenharia) continua abrindo — "ver e exportar"
  precisa continuar funcionando, e com 1-5 travados os dados que chegam lá
  não mudam mais. Dentro do próprio Card 6, `GeradorOrcamento.jsx` recebe o
  mesmo `bloqueadoTrial`: trava checklist de materiais/equipamentos, "Limpar
  Tudo", "Gerar Planilha de Cotação", "Gerar Proposta ao Cliente", preço
  manual de item sem preço + recalcular, confirmação do modal de escolha de
  cotação — mas **"Aprovar Lista e Gerar Orçamento" fica de propósito sem
  trava**: é o único jeito de abrir a seção de export (Excel/PDF da Lista de
  Engenharia fica atrás de `listaAprovada`, um `useState` local que não
  persiste — precisa clicar toda vez que o Card 6 abre); travar esse botão
  quebrava a exportação inteira (achado testando a jornada completa antes
  de commitar). Como o checklist já está congelado, clicar nele só expõe
  pra visualização o que já estava fixo, sem deixar mudar nada.
- **Fora do escopo desta trava:** `suspensa`/`cancelada` continuam sem
  enforcement real no backend (a property `Empresa.ativa` existe mas nunca
  é chamada).
- **Pendente:** a função de ativação de assinatura
  (`ativar_assinatura(empresa_id, plano, dias)`) que o admin e o futuro
  webhook do checkout de terceiro vão chamar — ainda não construída,
  `assinatura.py` é o lugar já preparado pra receber.
- Rotina de smoke test: `backend/scripts/validar_producao.py` (HTTP puro,
  só leitura) — roda antes de qualquer deploy/decisão que dependa do estado
  de produção.

Detalhe completo da decisão e da implementação: ver `project-jornada-assinatura-saas`
na memória, seção "IMPLEMENTADO 2026-08-25".

---

## Banco de Dados — Migrations (0001→0029)

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
| 0027 | Tabela `perfil_metalico` (catálogo global de perfis metálicos, multi-fabricante) |
| 0028 | Tabelas `selante_montagem`/`rebite`/`parafuso_bucha` + campos `largura_aba_padrao_mm`/`rendimento_selante_m_por_embalagem` em `configuracao_montagem` (kit de montagem) |
| 0029 | Seed de dados reais do kit de montagem em produção: 91 perfis MBP Isoblock + selante/rebite/parafuso+bucha (fabricante genérico) |
| 0030 | Tabela `apelido_fornecedor_item` — apelidos aprendidos por fornecedor (importação de cotação em PDF via IA) |
| 0031 | Amplia `cotacao_item.obs_fornecedor` de 250 para 500 caracteres (explicações de substituição geradas pela IA passavam do limite) |
| 0032 | Tabela `catalogo_generico` (cadastro genérico compartilhado, por `tipo_item`) + seed dos 3 itens da barreira de vapor (Lona Val Film, Fita Branca, Lona) |
| 0033 | Campo `empresa.recursos_avancados_habilitados` (boolean, default false) — trava opcional de Classificação de Itens / Catálogo de Preços |
| 0034 | Campo `usuario.telefone` (nullable) — captura celular/WhatsApp no cadastro público, vira lead pro time de vendas |

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
| `/api/v1/catalogo/perfis-metalicos` | GET | Perfis metálicos (seleção manual do kit de montagem, Card 1) |
| `/api/v1/gabinete` | POST | Cálculo câmara: lista_corte + materiais + kit de montagem (perfis/selante/rebite/parafuso) |
| `/api/v1/carga-termica` | POST | Cálculo kcal/h (Card 2) |
| `/api/v1/selecao` | POST | Busca UC + Evaporadora (Card 3) |
| `/api/v1/tubulacao` | POST | Dimensionamento ASHRAE (Card 4) |
| `/api/v1/componentes` | POST | Separadores + Válvula de Expansão (VET) do banco (Card 5) |
| `/api/v1/solenoide/selecionar` | POST | Seleção EVR v2 por Kv (Card 5) |
| `/api/v1/acessorios/selecionar` | POST | Filtro DML/DMC + Visor SGN (Card 5) |
| `/api/v1/carga-fluido/estimar` | POST | Estimativa carga fluido em kg (Card 5) |
| `/api/v1/tanque-liquido/selecionar` | POST | Tanque vertical NBR 16.069 (Card 5) |
| `/api/v1/cavalete/analisar` | POST | Luvas, porcas, reduções + válvulas de bloqueio GBC (Card 5) |
| `/api/v1/embalagem-fluido` | GET | Catálogo de embalagens de fluido por fluido (Card 6) |
| `/api/v1/orcamento` | POST | Consolidação orçamento (Card 6) — sem auth, de propósito |
| `/api/v1/produto-empresa/*` | GET/POST/PATCH/DELETE | Lista de preços — autoadministração (Fase B) |
| `/api/v1/classificacoes` | GET/POST | Árvore de classificação (blocos/tipos) |
| `/api/v1/cotacoes/*` | GET/POST/PATCH | Geração/importação planilha Excel + importação de PDF via IA (ver seção própria abaixo) |
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

### Importação de cotação em PDF via IA (em produção desde 2026-09-01)

Caminho alternativo à Fase 2 (planilha Excel) para fornecedores que devolvem a
cotação no PDF do próprio formato deles, sem preencher a planilha padrão.
Arquivos: `backend/app/services/cotacao_pdf.py` (chamada à IA),
`backend/app/models/apelido_fornecedor_item.py`, rotas em
`backend/app/api/routes_cotacao.py`.

- **Fluxo:** `POST /{cotacao_id}/importar/analisar-pdf` (upload do PDF, lê via
  IA — modelo `claude-sonnet-5`, chamada assíncrona) → mesmo relatório de
  conferência da planilha (`ok`/`sem_preco`/`nao_encontrado`/`linha_extra`) +
  um status novo, `possivel_substituicao` (a IA nunca decide sozinha uma
  substituição, só sinaliza pro humano revisar) → usuário confirma no mesmo
  endpoint da planilha, `POST /{cotacao_id}/importar/confirmar`. Nada é
  gravado antes da confirmação.
- **Cotação escolhida explicitamente pela URL** — diferente da planilha (que
  se autoidentifica pelo código embutido no arquivo), o PDF do fornecedor não
  carrega nosso código.
- **Apelidos por fornecedor (`apelido_fornecedor_item`, migration 0030):**
  regime permanente do casamento híbrido — a IA só resolve o cold start
  (termo nunca visto daquele fornecedor); uma vez o humano confirmando na
  tela de conferência (campo `termo_fornecedor` em `ItemConfirmacao`), o par
  `(fornecedor_id, termo_fornecedor)` vira lookup direto nas próximas
  cotações do mesmo fornecedor, sem chamar a IA de novo pra esse termo.
- `cotacao_item.obs_fornecedor` ampliado pra 500 caracteres (migration 0031)
  — as explicações de possível substituição geradas pela IA passavam fácil
  dos 250 caracteres pensados originalmente pra uma anotação manual curta.

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
3. **Catálogo de componentes no banco:** separadores de líquido/óleo e VET vêm do banco via `/api/v1/componentes` (busca direta por fluido/T.Evap/capacidade). Filtro secador, solenoide e visor são calculados/selecionados por algoritmo próprio (não busca direta no banco)
4. **Catálogo global × catálogo da empresa:** o catálogo técnico (equipamentos, componentes) é global e gerenciado pelo admin SaaS, só especificação, sem preço. Preços e códigos internos por empresa ficam em `produto_empresa` — **Fase B** (ver seção própria acima)
5. **Campo `temp_condensacao` no banco** armazena T.Amb conforme publicado nos catálogos dos fabricantes brasileiros. T.Cond real = T.Amb + ΔT (nunca assumir fixo)
6. **Alinhamento de grades de campos** (Cards 1-3, padrão fixado em 2026-08-31): rótulo `min-h-[40px]`, campo principal `h-11`, campo secundário (ex: linha de "horas") `h-9` — evita desalinhamento quando um rótulo quebra em 2 linhas e o vizinho não, ou quando nem todo campo da grade tem uma segunda linha (ex: stepper vs input simples)

---

## Catálogo Técnico

Painéis, unidades condensadoras, evaporadoras e portas frigoríficas vêm de
múltiplos fabricantes (Elgin, Danfoss Optyma, Mipal, Isoeste/MBP). Novo
fornecedor = preencher um dos templates na raiz (`template_paineis_frigorificos.xlsx`,
`template_unidades_condensadoras.xlsx`, `template_evaporadoras.xlsx`,
`template_portas_frigorificas.xlsx`) e rodar o importador correspondente em
`backend/scripts/` (`importar_paineis.py`, `importar_equipamentos.py`,
`importar_portas.py`) — upsert idempotente por chave única, nunca duplica.
Rodar local primeiro, depois em produção com `DATABASE_URL` do Render na env
(nunca colar a credencial no chat).

**Portas frigoríficas (em produção desde 2026-09-02):** catálogo real
inaugurado com 24 portas MBP Isoblock (proposta 084830) — antes só existiam
2 linhas placeholder sem fabricante. `PortaFrigoriifica` não tem
`UniqueConstraint` no banco — o upsert do importador usa como chave
`fabricante + tipo + classificacao + largura + altura + espessura + batente
+ abertura` (checado em código, mesmo padrão do `importar_paineis.py`).
`batente` (3B/4B) e `soleira` são campos **independentes** — não presumir
uma regra fixa entre eles sem confirmar com o fabricante.

Classificação de itens do orçamento é via banco (`bloco_orcamento`,
`classificacao_item`, `item_classificacao`), servida por `GET
/api/v1/classificacoes`. Todos os geradores (gabinete, tubulação, cavalete,
componentes, equipamentos, portas) emitem `tipo_item` (slug estável) — **não
existe mais classificação por string-matching no frontend**. Editável sem
deploy pela página "Classificação de Itens" no menu lateral.

Rate-limiting da API foi adiado de propósito para pré-lançamento (ver
`project-auditoria-20260708` na memória).

---

## Estado atual do código (auditado em 2026-09-02)

| Funcionalidade | Status |
|---------------|--------|
| Wizard 6 cards | ✅ funcional |
| Autenticação JWT | ✅ |
| Gabinete + painéis PIR Kingspan + portas | ✅ |
| Card 1 — Kit de Montagem (perfis/selante/rebite/parafuso+bucha) | ✅ em produção desde 2026-09-01, catálogo real (91 perfis MBP Isoblock) desde 2026-09-01 |
| Card 1 — Barreira de Vapor (Lona Val Film/Fita Branca/Lona) | ✅ em produção desde 2026-09-02, fórmulas confirmadas com o autor da planilha de referência |
| Carga térmica | ✅ campos de horas (iluminação/ocupação/motores) e margem de segurança editáveis desde 2026-08-31 |
| Seleção UC + Evaporadora | ✅ interpolação bilinear T.Ambiente × T.Evap desde 2026-08-31 |
| Tubulação ASHRAE + isolamento Armacel | ✅ |
| Card 5 — Separadores (banco de dados) | ✅ |
| Card 5 — VET automática (banco de dados) | ✅ desmembrada em corpo+orifício na lista desde 2026-08-31 |
| Card 5 — Solenoide automático (R404A/R22) | ✅ motor Kv; desmembrado em válvula+bobina na lista desde 2026-08-31 |
| Card 5 — Filtro secador automático (DML/DMC) | ✅ |
| Card 5 — Visor de líquido automático (SGN) | ✅ |
| Card 5 — Tanque de Líquido (NBR 16.069) | ✅ |
| Card 5 — Carga de Fluido (kg por trecho) | ✅ |
| Card 5 — Cavalete (luvas/porcas/reduções + válvulas GBC) | ✅ |
| Card 5 — Modo Engenharia (CoolSelector) | ✅ |
| Card 6 — Embalagem de fluido (Card 6, converte kg em cilindros) | ✅ só R404A tem dado real |
| Insight de estimativa de capacidade (coluna esquerda) | ✅ informativo, nunca usado em cálculo |
| Insight "Renovação de Ar" (trocas/h, Painel Resumo Lateral) | ✅ fix 2026-09-01: somava vazão do condensador da UC junto com a do evaporador, inflando o número — corrigido filtrando por `categoria === 'Evaporadora'` |
| Projeto CAD (.DXF, Card 1) | ✅ reescrito 2026-09-01 com `ezdxf` — cotas reais (DIMENSION), altura, juntas nas 4 paredes, vistas Frontal/Lateral. Posição da porta na parede fica de fora (dado não capturado no wizard) |
| Orçamento + Cotação Excel + Proposta PDF | ✅ |
| Verificação de cotação antes de gerar proposta | ✅ funcional, ajustes pendentes |
| Revisão manual de quantidade/substituição antes da proposta (Card 6) | ✅ em produção desde 2026-09-02, persistida em `dados_completos` |
| Importação de cotação em PDF via IA (com apelidos por fornecedor) | ✅ em produção desde 2026-09-01 |
| Proposta com preços da cotação (via preco_unitario) | ✅ |
| Modal resumo ao carregar projeto | ✅ |
| Aviso "pode estar desatualizado" nos cards | ✅ |
| Salvar/Carregar projeto (dados_completos) | ✅ |
| Configurações de montagem (perfis) | ✅ |
| Gestão de clientes | ✅ |
| Diagrama SVG do cavalete (flutuante) | ✅ |
| Multi-tenancy — empresa/papéis/isolamento (Fase A) | ✅ em produção desde 2026-08-05 |
| Recursos avançados por empresa (Classificação/Catálogo de Preços) | ✅ em produção desde 2026-09-02, só trava no frontend (sem gate no backend, de propósito) |
| Limite de sessões + logout real + métrica IP (admin) | ✅ em produção desde 2026-08-19 |
| Lista de Engenharia exportável (Excel/PDF) — Card 6 | ✅ em produção desde 2026-08-19 |
| Catálogo/lista de preços por empresa (Fase B) | ✅ em produção desde 2026-08-20 |
| Trial 15 dias/1 projeto — trava real de edição | ✅ backend (Save) desde 2026-08-25; frontend (Cards 1-5, recalcular) desde 2026-08-31 |
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

### Revisão manual antes de gerar a proposta (em produção desde 2026-09-02)

Painel **sempre visível** (`🔍 Revisão antes de gerar a proposta`, `GeradorOrcamento.jsx`)
logo abaixo dos botões "Gerar Planilha de Cotação"/"Gerar Proposta ao Cliente" — por
decisão do usuário, pra virar hábito de conferência, não só aparecer quando falta preço.
Resolve dois problemas reais encontrados usando a importação de cotação em PDF: o
fornecedor cota por embalagem diferente da unidade dimensionada (ex: sistema calcula
870 un de rebite, fornecedor vende em pacote de 500 e cotou 2 pacotes — multiplicar
870 × preço do pacote distorce o total), e o fornecedor sugere um item equivalente de
outro modelo/fabricante.

- **Correção de quantidade**: input numérico por item (placeholder = quantidade
  calculada). Aplicado só na hora de montar o payload do orçamento
  (`qtdCorrigida()` em `gerarOrcamentoComPrecos`) — a quantidade "real" calculada
  pelos Cards 1-5 nunca é alterada, só o número que vai pro orçamento/proposta.
- **Substituição de item**: quando a cotação trouxe `marca_modelo_cotado`
  (preenchido na confirmação da importação, manual ou por IA) diferente da
  descrição do item, aparece como sugestão com checkbox — marcar troca o nome do
  item na proposta ao cliente (`nomeCorrigido()`), mantendo o item do
  dimensionamento técnico intacto por trás.
- **Zero mudança de backend/schema** — `ItemOrcamento.qtde`/`.item`
  (`backend/app/schemas/orcamento.py`) já aceitavam qualquer valor vindo do
  frontend sem validação nenhuma contra os valores calculados; a correção inteira
  é resolvida no frontend, no payload que vai pro `POST /api/v1/orcamento`.
- **Persistência entre save/reload** (pedido explícito do usuário — evitar refazer
  a mesma revisão toda vez que o projeto reabre): `precosManuals`, `qtdesManuais`
  e `itensSubstituidos` (todos `Map<norm(descricao), valor>`) entram no mesmo
  `onValoresChange` que já persiste o resto do Card 6 em `dados_completos`: —
  restaurados via `initialValues` ao reabrir o projeto salvo, reaplicados
  automaticamente ao gerar a proposta de novo, sem precisar redigitar.
- **Risco conhecido, aceito por ora**: mesma fragilidade de casamento por
  `norm(descricao)` das seções acima — se a descrição do item mudar entre
  gerações (ex: editar o Card que gerou aquele item), a correção salva não casa
  mais. Mitigação fica para uma revisão futura (não bloqueante pro lançamento
  desta funcionalidade).

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
