# 06 - Deploy Vercel + Render

Este documento define as premissas de deploy e operacao para o projeto V2.

## 1. Objetivo

Padronizar um caminho simples e economico de producao para o SaaS:

- Frontend em Vercel.
- Backend FastAPI em Render.
- Banco PostgreSQL em Render.

## 2. Arquitetura de Deploy

| Camada | Plataforma |
|---|---|
| Frontend | Vercel |
| Backend API | Render Web Service |
| Banco de dados | Render PostgreSQL |

## 3. Premissas Operacionais

1. Aplicacao backend deve ser stateless.
2. Persistencia deve ficar no PostgreSQL.
3. Configuracao deve ser feita por variaveis de ambiente.
4. CORS deve aceitar apenas dominio(s) do frontend publicado.
5. Toda mudanca de producao deve passar por GitHub.

## 4. Seguranca e Dados

- Nao commitar segredos no repositorio.
- Usar secrets nos paineis do Vercel/Render.
- Ativar backup do banco.
- Planejar politica de retencao e restauracao.

## 5. Custo e Escalabilidade

- Comecar com plano de menor custo compativel com producao inicial.
- Acompanhar uso de CPU, memoria, conexoes e armazenamento.
- Escalar somente com base em metricas reais de uso.

## 6. Artefatos no Repositorio

- `infra/render.yaml`: blueprint inicial para backend e banco no Render.
- `infra/vercel.md`: configuracao base esperada para o frontend no Vercel.
- `backend/.env.example`: variaveis esperadas do backend.
- `frontend/.env.example`: variaveis esperadas do frontend.
