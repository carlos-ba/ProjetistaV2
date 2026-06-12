# ProjetistaV2 — IceNexus IAR

Sistema SaaS de dimensionamento e orçamento para câmaras frigoríficas.

## Visão Geral

O ProjetistaV2 guia o técnico de refrigeração por um roteiro completo:

1. **Gabinete** — dimensões, painéis frigoríficos (catálogo), portas, tipo de piso
2. **Carga Térmica** — cálculo das cargas por paredes/teto/piso, infiltração, produto, respiração, pessoas, iluminação, motores
3. **Seleção de Equipamentos** — busca no catálogo por temperatura de evaporação e condensação, interpolação de capacidade
4. **Componentes e Acessórios** — separadores de óleo, filtros, VETs, válvulas, etc.
5. **Tubulação** — dimensionamento de linhas (sucção, líquido, descarga) pelo método ASHRAE
6. **Orçamento** — geração de lista de materiais, cotação com fornecedores, proposta comercial

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 async + Alembic |
| Banco | PostgreSQL (local 17 / produção Render 18) |
| Driver | psycopg3 (`postgresql+psycopg://`) |
| Frontend | React 19 + Vite + Tailwind CSS + shadcn/ui |
| Deploy backend | Render (auto-deploy no push para `main`) |
| Deploy frontend | Vercel (auto-deploy no push para `main`) |

## URLs

| Serviço | URL |
|---|---|
| Frontend | https://projetista-v2.vercel.app |
| Backend API | https://projetista-v2-api-alt.onrender.com |
| API Docs | https://projetista-v2-api-alt.onrender.com/docs |
| GitHub | https://github.com/carlos-ba/ProjetistaV2 |

## Estrutura do Repositório

```
backend/         API FastAPI
frontend/        React + Vite
scripts/         Scripts de importação e manutenção do banco
infra/           Configurações de deploy
tests/           Testes de integração/E2E
```

## Rodando Localmente

### Backend

```powershell
cd backend
..\.venv\Scripts\python.exe ..\run.py
```

> Usar `run.py` é obrigatório no Windows — ele configura `asyncio.WindowsSelectorEventLoopPolicy` antes de iniciar o uvicorn (evita erro ProactorEventLoop com psycopg3).

### Frontend

```powershell
cd frontend
npm run dev
```

## Banco de Dados

### Banco local

```powershell
$env:PGPASSWORD = "projetista"
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U projetista -p 5432 -d projetista_v2
```

### Sincronizar produção → local

```powershell
cd backend
& "..\venv\Scripts\python.exe" ..\scripts\copiar_prod_para_local.py
```

### Migrations

As migrations rodam automaticamente no start do Render (`alembic upgrade head && uvicorn ...`).

Para rodar localmente:

```powershell
cd backend
..\.venv\Scripts\alembic.exe upgrade head
```

## Protocolo de Sessão

**Início:** `git pull` + `copiar_prod_para_local.py`

**Fim:** `git push` (se houve mudança de código)

**Regra:** produção é sempre a fonte de verdade para dados.

## Migrations

| Versão | Conteúdo |
|---|---|
| 0001 | Schema completo v2 |
| 0002 | Verificação de e-mail no usuário |
| 0003 | Campo consumo_kw na performance |
| 0004 | Temperatura ambiente na performance de equipamento |
| 0005 | Painel frigorífico |
| 0006 | Isolamento de tubulação |
| 0007 | Porta frigorífica |
| 0008 | Cotação com fornecedor (fornecedor, cotacao, cotacao_item) |
| 0009 | Proposta comercial |
