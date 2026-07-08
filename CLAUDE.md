# CLAUDE.md — ProjetistaV2

Leia este arquivo no início de toda sessão. Ele descreve o estado real do projeto,
como rodar localmente, convenções adotadas e o que está pendente de implementar.

---

## Identidade do Produto

**IceNexus IAR** — SaaS de dimensionamento frigorífico para técnicos e engenheiros de refrigeração.
Substitui planilhas manuais por um wizard guiado de 6 etapas.

---

## Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI + SQLAlchemy 2.0 async + PostgreSQL + Alembic |
| Driver DB | psycopg3 (`psycopg[binary]`) — string: `postgresql+psycopg://` |
| Frontend | React 19 + Vite + Tailwind CSS + shadcn/ui |
| Deploy backend | Render (auto-deploy no push para `main`) |
| Deploy frontend | Vercel (auto-deploy no push para `main`) |
| Migrations | Alembic (0001→0016), roda no `startCommand` do Render |

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
| 6 | `GeradorOrcamento.jsx` | Geração de orçamento + cotação Excel + proposta comercial PDF |

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

## Banco de Dados — Migrations (0001→0016)

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

---

## Endpoints Backend (20 rotas)

| Endpoint | Método | Função |
|----------|--------|--------|
| `/api/v1/auth/*` | POST/GET | Autenticação JWT |
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
| `/api/v1/cavalete/analisar` | POST | Luvas, porcas, reduções (Card 5) |
| `/api/v1/orcamento` | POST | Consolidação orçamento (Card 6) |
| `/api/v1/cotacao/*` | GET/POST/PATCH | Geração/importação planilha Excel |
| `/api/v1/proposta/*` | GET/POST | Proposta comercial PDF |
| `/api/v1/configuracoes/montagem` | GET/POST | Perfis de montagem (tipo filtro, visor, trechos) |
| `/api/v1/health` | GET | Health check |

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
4. **Catálogo global × catálogo da empresa:** o catálogo técnico (equipamentos, componentes) é global e gerenciado pelo admin SaaS. Preços e códigos internos por empresa ficam em tabelas separadas — implementar na Fase 2
5. **Campo `temp_condensacao` no banco** armazena T.Amb conforme publicado nos catálogos dos fabricantes brasileiros. T.Cond real = T.Amb + ΔT (nunca assumir fixo)

---

## Estado atual do código (2026-06-29)

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
| Card 5 — Cavalete (luvas/porcas/reduções) | ✅ |
| Card 5 — Modo Engenharia (CoolSelector) | ✅ |
| Orçamento + Cotação Excel + Proposta PDF | ✅ |
| Verificação de cotação antes de gerar proposta | ✅ funcional, ajustes pendentes |
| Proposta com preços da cotação (via preco_unitario) | ✅ |
| Modal resumo ao carregar projeto | ✅ |
| Aviso "pode estar desatualizado" nos cards | ✅ |
| Salvar/Carregar projeto (dados_completos) | ✅ |
| Configurações de montagem (perfis) | ✅ |
| Gestão de clientes | ✅ |
| Diagrama SVG do cavalete (flutuante) | ✅ |
| Admin panel / multi-tenancy | ❌ Fase 2 |
| IA com Tool Use | ❌ Fase 3 |
| Billing | ❌ Fase 5 |

---

## Fluxo de Verificação de Cotação — Card 6 (implementado 2026-06-29)

### Lógica ao clicar "💰 GERAR PROPOSTA AO CLIENTE"

1. Busca `GET /api/v1/cotacoes?projeto_id={id}` filtrando status ≠ `cancelada`
2. **Nenhuma cotação** → aviso âmbar + botões para gerar planilha ou abrir painel de cotações
3. **Cotação(ões) mas nenhuma `processada`** → aviso azul com código(s) + botão para abrir painel
4. **1 cotação `processada`** → gera direto com os preços dela
5. **2+ cotações `processadas`** → modal de escolha: uma específica OU "Melhor preço por item" (min entre todas)

### Injeção de preços

- O frontend busca `GET /api/v1/cotacoes/{id}` para cada cotação selecionada
- Constrói um `precoMap: Map<norm(descricao), preco>` (casamento por descrição normalizada, igual ao `casar_itens()` do backend)
- Injeta `preco_unitario` em cada item do payload do orçamento
- O backend (`backend/app/schemas/orcamento.py`) aceita `preco_unitario: float | None` em `ItemOrcamento`
- O serviço (`backend/app/services/orcamento.py`) usa esse valor se presente; fallback para `Material.custo`/`Equipamento.custo`

### Itens sem preço

- Itens não encontrados na cotação ficam com `preco_unitario=null` → backend retorna `custo_unitario_rs=0`
- Após gerar, aparece seção âmbar com lista dos itens sem preço + inputs para preço manual
- Botão "Recalcular" regenera a proposta usando `ultimoPrecoMapRef` (preços da cotação) + preços manuais como override

### Pendências conhecidas (retomar aqui)

- Ajustes de lógica identificados pelo usuário — **não detalhados antes da pausa**, retomar com testes
- O casamento por descrição pode falhar se a descrição gerada no orçamento diferir da descrição gravada na cotação (ex: complementos livres, itens do gabinete com área no detalhe)
- Fluxo de gestão de cotações ainda simples — módulo dedicado planejado para Fase 2

### Arquivos modificados nesta sessão (2026-06-29)

| Arquivo | O que mudou |
|---------|------------|
| `backend/app/schemas/orcamento.py` | `ItemOrcamento` ganhou `preco_unitario: float \| None = None` |
| `backend/app/services/orcamento.py` | Usa `preco_unitario` do payload quando presente, fallback para banco |
| `frontend/src/components/GeradorOrcamento.jsx` | `verificarEGerar`, `gerarOrcamentoComPrecos`, `_gerarComCotacoes`, modal de escolha, aviso de itens sem preço, inputs manuais |
| `frontend/src/App.jsx` | Prop `onAbrirPainelCotacoes` passada para Card 6 |
