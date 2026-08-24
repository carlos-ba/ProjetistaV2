# Infra

Configurações de infraestrutura e deploy.

## Deploy

| Serviço | Plataforma | Trigger |
|---|---|---|
| Frontend | Vercel | Push para `main` |
| Backend | Render (`projetista-v2-api-alt`) | Push para `main` |
| Banco | Render (`projetista-v2-db`, PostgreSQL) | — |

## Render — Backend

- **Região:** Oregon
- **Start command:** `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Build command:** `pip install -r requirements.txt`

## Banco de Dados — Produção

- **Nome:** `projetista_v2_wchd`
- **Usuário:** `projetista`
- **Host:** `dpg-d8iovfrtqb8s73bdolf0-a.oregon-postgres.render.com`
- **PostgreSQL:** 18

## Variáveis de Ambiente (Render)

Configuradas no dashboard do Render:
- `DATABASE_URL`
- `SECRET_KEY`
- `CORS_ORIGINS`
- `FRONTEND_URL`

## CORS

Origens permitidas durante a migração:

- `https://camara-fria.icenexus.com.br`
- `https://www.icenexus.com.br`
- `https://icenexus.com.br`
- `https://projetista-v2.vercel.app`

O `FRONTEND_URL` de produção aponta para `https://camara-fria.icenexus.com.br`.
