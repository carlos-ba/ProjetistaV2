# 08 - Status Atual

Data de referencia: 2026-04-28

## 1. Ambiente Publicado

- Frontend (Vercel): `https://projetista-v2-frontend.vercel.app`
- Backend (Render): `https://projetista-v2-api-alt.onrender.com`
- Swagger backend: `https://projetista-v2-api-alt.onrender.com/docs`

## 2. Recursos Ativos

Render:

- `projetista-v2-db` (Postgres)
- `projetista-v2-api-alt` (Web Service Python)

Vercel:

- `projetista-v2-frontend`

## 3. Configuracao Atual

Backend (Render):

- `APP_ENV=production`
- `DATABASE_URL` configurada no painel do Render
- `CORS_ORIGINS=https://projetista-v2-frontend.vercel.app`

Frontend (Vercel):

- `NEXT_PUBLIC_API_URL=https://projetista-v2-api-alt.onrender.com`

## 4. Validacoes Executadas

- Frontend responde HTTP 200 em producao.
- Backend `/docs` responde HTTP 200.
- Deploy manual do backend concluido com status `live`.

## 5. Decisoes Confirmadas

- Plataforma inicial de deploy: `Vercel + Render`.
- Backend e frontend mantidos separados.
- Persistencia de dados em PostgreSQL gerenciado.

## 6. Riscos/Pontos de Atencao

- Ainda nao existe modelagem de banco implementada.
- Ainda nao existem endpoints de negocio publicados.
- Pendências críticas de requisitos aguardando resposta do responsável (ver seção 8 de `01_requisitos.md`).

## 7. Checkpoint Git

- Branch: `main`
- Commit de referencia de infraestrutura inicial publicada: `3ef42f9`

---

## 8. Checkpoint de Sessão — 2026-04-28

### O que foi feito nesta sessão

1. **Análise SDD realizada:** O projeto foi avaliado quanto à conformidade com o modelo SDD.
   - Resultado: estrutura correta, mas documentos de especificação estavam vazios (placeholders).

2. **`docs/01_requisitos.md` criado e estruturado** com:
   - Visão geral do produto
   - Perfil de usuário MVP
   - 6 requisitos funcionais (RF-01 a RF-06)
   - 6 requisitos não funcionais (RNF-01 a RNF-06)
   - Fluxo principal do usuário
   - Itens fora do escopo do MVP
   - Tabela de pendências críticas para início do desenvolvimento

### Estado atual da documentação SDD

| Arquivo | Status |
|---|---|
| `docs/00_visao_geral.md` | Completo |
| `docs/01_requisitos.md` | Estruturado — aguarda respostas das pendências P1 a P5 |
| `docs/02_arquitetura.md` | Mínimo — aguarda detalhamento |
| `docs/03_banco_de_dados.md` | Placeholder — bloqueado por P1/P2/P3 |
| `docs/04_api.md` | Placeholder — bloqueado por P2/P3/P4 |
| `docs/05_frontend.md` | Placeholder — bloqueado por P2/P4 |
| `docs/06_deploy_vercel_render.md` | Completo |
| `docs/07_decisoes_tecnicas.md` | 1 decisão registrada |

### Próxima ação ao retomar

1. Abrir `docs/01_requisitos.md` seção 8 (Pendências Críticas).
2. Responder as perguntas P1 a P5 — especialmente **P1 (domínio do sistema)** e **P3 (lógica de cálculo)**.
3. Com P1–P5 respondidas, preencher `docs/03_banco_de_dados.md` e `docs/04_api.md`.
4. Só então iniciar código de negócio no backend.
