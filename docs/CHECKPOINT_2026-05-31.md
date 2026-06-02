# CHECKPOINT — 31/05/2026
## Projetista V2 — Estado atual do desenvolvimento

---

## ✅ O QUE FOI FEITO HOJE

### Fase 1 — Segurança & Auth (CONCLUÍDA)

| Item | Arquivo | Status |
|---|---|---|
| SECRET_KEY obrigatória em produção | `backend/app/core/config.py` | ✅ |
| CORS seguro (sem `["*"]`) | `backend/app/core/config.py` | ✅ |
| Email verification no cadastro | `backend/app/api/routes_auth.py` | ✅ |
| Endpoint `/verify-email/` | `backend/app/api/routes_auth.py` | ✅ |
| Endpoint `/forgot-password/` | `backend/app/api/routes_auth.py` | ✅ |
| Endpoint `/reset-password/` | `backend/app/api/routes_auth.py` | ✅ |
| Serviço de email (aiosmtplib) | `backend/app/services/email.py` | ✅ |
| Migration 0002 (novos campos usuario) | `backend/alembic/versions/0002_...py` | ✅ |
| Fix Windows ProactorEventLoop | `backend/run.py` | ✅ |
| Fix bcrypt 4.0.1 incompatibilidade | `backend/requirements.txt` | ✅ |
| .env local configurado | `backend/.env` | ✅ |

### Ambiente Local (FUNCIONANDO)

| Serviço | URL | Status |
|---|---|---|
| Frontend React (Vite) | http://localhost:5173 | ✅ |
| Backend FastAPI | http://localhost:8000 | ✅ |
| Swagger UI | http://localhost:8000/docs | ✅ |
| PostgreSQL (Docker) | localhost:5432 | ✅ |

### Banco de Dados — Dados de teste carregados

| Tabela | Registros |
|---|---|
| unidade_medida | 6 |
| fabricante | 7 |
| categoria | 13 |
| tipo_produto_termico | 9 |
| perfil_produto_termico | 26 |
| equipamento | 18 |
| performance_equipamento | 85 |
| material | 25 |
| componente_tecnico | 32 |

### Fix API — perfis-produto retorna objeto `tipo` completo
- Arquivo: `backend/app/schemas/catalogo.py`
- Arquivo: `backend/app/services/catalogo.py`
- Problema: frontend esperava `p.tipo?.nome` mas API retornava só `tipo_id`
- Solução: `selectinload(PerfilProdutoTermico.tipo)` no service + campo `tipo` no schema

### Documentação e Ferramentas geradas
- `docs/GUIA_CADASTRO_BANCO.md` — Estrutura detalhada de todas as tabelas
- `scripts/seed_dados.sql` — Seed com dados de teste
- `scripts/cadastro_banco_projetista.xlsx` — Planilha Excel modelo para cadastro real
- `scripts/gerar_planilha_cadastro.py` — Script que gerou a planilha

---

## ⏳ PRÓXIMO PASSO IMEDIATO

### Quando voltar — começar aqui:

**1. Preencher a planilha com dados reais**
- Arquivo: `scripts/cadastro_banco_projetista.xlsx`
- Abrir no Excel e preencher com equipamentos e dados reais dos catálogos dos fabricantes
- A aba mais crítica é `7️⃣ Performance Equip.` — dados do catálogo técnico (kcal/h por temperatura)

**2. Criar script de importação da planilha → banco**
- Ler o Excel preenchido e gerar SQL / importar direto no PostgreSQL
- Script a criar: `scripts/importar_planilha.py`

---

## 🗺️ ROADMAP COMPLETO

```
✅ Fase 1 — Segurança & Auth          CONCLUÍDA
⏳ Fase 2 — PDF + Admin panel          PRÓXIMA
⏳ Fase 3 — Integração com IA (Tool Use)
⏳ Fase 4 — Testes locais completos
⏳ Fase 5 — Deploy (Render + Vercel)
⏳ Fase 6 — Billing (Stripe/PagSeguro)
```

### Fase 2 — O que fazer:
- [ ] Exportação PDF: memorial de cálculo + proposta comercial
- [ ] Admin panel: CRUD de equipamentos, materiais, componentes
- [ ] Admin panel: gestão de usuários
- [ ] Admin panel: métricas de uso

---

## 🚀 COMO RETOMAR O AMBIENTE LOCAL

```powershell
# 1. Iniciar Docker Desktop (ícone na bandeja do sistema)

# 2. Subir o banco de dados
docker-compose up -d db

# 3. Iniciar o backend (no terminal do PyCharm, raiz do projeto)
.\scripts\run_backend.ps1

# 4. Iniciar o frontend (em outro terminal)
cd frontend
npm run dev

# 5. Acessar
# Frontend:  http://localhost:5173
# Swagger:   http://localhost:8000/docs
```

### Credenciais de teste
| Campo | Valor |
|---|---|
| Usuário | `teste_local` |
| Senha | `senha123` |

---

## 📁 ARQUIVOS IMPORTANTES MODIFICADOS HOJE

```
backend/
├── app/
│   ├── core/config.py          ← SECRET_KEY + CORS validados
│   ├── main.py                 ← Fix Windows SelectorEventLoop
│   ├── api/routes_auth.py      ← +verify-email, +forgot/reset-password
│   ├── services/
│   │   ├── auth.py             ← lógica de verificação e reset
│   │   ├── email.py            ← NOVO — envio de emails
│   │   └── catalogo.py         ← Fix selectinload tipo
│   ├── schemas/
│   │   ├── auth.py             ← +email_verified, +ForgotPassword, +ResetPassword
│   │   └── catalogo.py         ← Fix PerfilProdutoTermicoOut com tipo aninhado
│   └── models/usuario.py       ← +email_verified, +tokens de verificação
├── alembic/versions/
│   └── 0002_usuario_email_verification.py  ← NOVA migration
├── requirements.txt            ← +aiosmtplib, +pydantic[email], bcrypt==4.0.1
├── run.py                      ← NOVO — entry point Windows
└── .env                        ← NOVO — ambiente local

scripts/
├── seed_dados.sql                    ← NOVO — dados de teste
├── gerar_planilha_cadastro.py        ← NOVO — gerador da planilha
└── cadastro_banco_projetista.xlsx    ← NOVO — planilha para dados reais

docs/
├── GUIA_CADASTRO_BANCO.md            ← NOVO
└── CHECKPOINT_2026-05-31.md          ← ESTE ARQUIVO
```
