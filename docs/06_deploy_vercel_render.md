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

## 7. Checklist de Publicacao (Sem Contas Criadas)

1. Criar conta no GitHub (se ainda nao tiver) e confirmar email.
2. Criar conta no Render usando login com GitHub.
3. Criar conta no Vercel usando login com GitHub.
4. No Render, adicionar metodo de pagamento para evitar bloqueios de recursos.
5. No Vercel, revisar plano atual e limites do plano gratuito.
6. No Render, conectar o repositorio `carlos-ba/ProjetistaV2`.
7. No Render, criar banco PostgreSQL gerenciado.
8. No Render, criar Web Service para o backend com `Root Directory = backend`.
9. Configurar no backend Render `Build Command` como `pip install -r requirements.txt`.
10. Configurar no backend Render `Start Command` como `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
11. Configurar variavel `APP_ENV=production` no backend Render.
12. Configurar variavel `DATABASE_URL` com a connection string do Postgres Render.
13. Configurar variavel `CORS_ORIGINS` com a URL do frontend Vercel quando existir.
14. Fazer primeiro deploy do backend e validar endpoint base (`/docs`).
15. No Vercel, importar o repositorio `carlos-ba/ProjetistaV2`.
16. Configurar `Root Directory` no Vercel como `frontend`.
17. Configurar variavel `NEXT_PUBLIC_API_URL` no Vercel apontando para a URL publica do backend Render.
18. Fazer deploy do frontend no Vercel.
19. Atualizar `CORS_ORIGINS` no Render com dominio final do frontend Vercel.
20. Validar comunicacao frontend -> backend.
21. Executar teste funcional basico abrindo frontend, enviando dados de exemplo, validando resposta de calculo e testando salvar/consultar.
22. Ativar backup e retencao do PostgreSQL no Render.
23. Configurar alertas de custo/uso nas duas plataformas.
24. Registrar no GitHub qualquer ajuste de configuracao feito em producao.

## 8. Checklist de Go-Live (Rapido)

1. Variaveis de ambiente revisadas.
2. CORS restrito ao dominio correto.
3. Banco com backup ativo.
4. Sem segredos no repositorio.
5. Aplicacao acessivel via HTTPS.
6. Fluxo principal do SaaS validado ponta a ponta.
