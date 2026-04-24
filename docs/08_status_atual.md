# 08 - Status Atual

Data de referencia: 2026-04-23

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
- Documento de requisitos ainda precisa ser detalhado.

## 7. Checkpoint Git

- Branch: `main`
- Commit de referencia de infraestrutura inicial publicada: `3ef42f9`
