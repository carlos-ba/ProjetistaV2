# 08 - Status Atual

Data de referência: 2026-06-28

---

## 1. Ambiente Publicado

- Frontend (Vercel): https://projetista-v2.vercel.app
- Backend (Render): https://projetista-v2-api-alt.onrender.com
- Swagger backend: https://projetista-v2-api-alt.onrender.com/docs

## 2. Recursos Ativos

Render:
- `projetista-v2-db` (Postgres)
- `projetista-v2-api-alt` (Web Service Python)

Vercel:
- `projetista-v2-frontend`

## 3. Configuração Atual

Backend (Render):
- `APP_ENV=production`
- `DATABASE_URL` configurada no painel do Render
- `CORS_ORIGINS=["https://projetista-v2.vercel.app"]`

Frontend (Vercel):
- `VITE_API_BASE_URL=https://projetista-v2-api-alt.onrender.com`

## 4. Estado das Funcionalidades

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
| Salvar/Carregar projeto com invalidação em cascata | ✅ |
| Configurações de montagem (perfis) | ✅ |
| Gestão de clientes | ✅ |
| Diagrama SVG do cavalete (flutuante) | ✅ |
| Admin panel / multi-tenancy | ❌ Fase 2 |
| IA com Tool Use | ❌ Fase 3 |
| Billing | ❌ Fase 5 |

## 5. Banco de Dados

- Migrations aplicadas: **0001 → 0016**
- Principais tabelas com dados reais:

| Tabela | Registros estimados |
|--------|-------------------|
| equipamento | 19 (7 UCs + 12 evaporadoras FL*) |
| performance_equipamento | 627 |
| componente_tecnico | 18 (VET + Separadores) |
| performance_componente | 128 |
| painel_frigorifico | 16 (Kingspan Isoeste PIR) |
| isolamento_tubulacao | 97 (Armacel D/F/H/M/R/T) |
| perfil_produto_termico | 26 (ASHRAE validado) |

## 6. Decisões Confirmadas

- Wizard linear de 6 cards como fluxo principal
- Backend stateless com estado persistido em `dados_completos` (JSONB) no projeto
- Catálogo técnico global (admin SaaS) — catálogo por empresa fica para Fase 2
- Auto-deploy via GitHub → Render (backend) + Vercel (frontend)

## 7. Checkpoint Git

- Branch: `main`
- Commits recentes relevantes:
  - `c83dc16` — planilha Excel com colunas metros + kg para tubos de cobre
  - `df578ff` — peso de tubos de cobre e seleção de espessura de parede
  - `134d768` — carregamento automático de projeto e invalidação em cascata
  - `3b611e3` — diagrama SVG dinâmico do cavalete de componentes
