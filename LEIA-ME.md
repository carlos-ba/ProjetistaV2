# Projetista 360 — IceNexus IAR
Sistema de dimensionamento de câmaras frigoríficas.

## Início rápido em um novo PC

### 1. Pré-requisitos
- [Python 3.14+](https://python.org)
- [Node.js 18+](https://nodejs.org)
- [Docker Desktop](https://docker.com)
- [Git](https://git-scm.com)

### 2. Setup (primeira vez)
```powershell
git clone https://github.com/carlos-ba/ProjetistaV2.git
cd ProjetistaV2
.\scripts\setup_novo_pc.ps1
```

### 3. Rodar o projeto
```powershell
.\scripts\rodar_local.ps1
```
Ou manualmente:
```powershell
docker-compose up -d db          # banco
.\scripts\run_backend.ps1        # backend (novo terminal)
cd frontend && npm run dev       # frontend (novo terminal)
```

### 4. Acessar
- **App:** http://localhost:5173
- **API:** http://localhost:8000/docs
- **Login local:** `teste_local` / `senha123`

---

## Produção
- **Frontend:** https://projetista-v2-frontend-carlos-bas-projects.vercel.app
- **Backend:** https://projetista-v2-backend.onrender.com

---

## Estrutura do projeto
```
ProjetistaV2/
├── backend/          ← FastAPI + PostgreSQL
│   ├── app/          ← código da API
│   ├── alembic/      ← migrations (0001→0007)
│   └── run.py        ← entry point Windows
├── frontend/         ← React + Vite + Tailwind + shadcn/ui
│   └── src/
│       ├── components/  ← módulos do wizard (6 cards)
│       └── pages/
├── scripts/          ← importação de dados e setup
│   ├── setup_novo_pc.ps1   ← setup completo
│   ├── rodar_local.ps1     ← iniciar o sistema
│   └── importar_*.py       ← scripts de importação Excel
├── docs/             ← checkpoints e decisões de arquitetura
└── infra/            ← render.yaml (deploy)
```

---

## Importar dados do catálogo
Os scripts de importação leem planilhas Excel:
```powershell
# Condensadoras
python scripts\importar_excel.py <arquivo.xlsx>

# Evaporadoras
python scripts\importar_evaporadoras.py <arquivo.xlsx>

# VET (válvulas)
python scripts\importar_vet.py <arquivo.xlsx>

# Separadores de líquido
python scripts\importar_separador.py <arquivo.xlsx>

# Painéis frigoríficos
python scripts\importar_paineis.py <arquivo.xlsx>

# Isolamento tubulação
python scripts\importar_isolamento.py <arquivo.xlsx>

# Portas frigoríficas
python scripts\importar_portas.py <arquivo.xlsx>
```

---

## Tecnologias
| Camada | Stack |
|---|---|
| Backend | FastAPI + SQLAlchemy + PostgreSQL + Alembic |
| Frontend | React 19 + Vite + Tailwind CSS + shadcn/ui |
| Deploy | Render (backend) + Vercel (frontend) |
| Banco local | Docker PostgreSQL 17 |
