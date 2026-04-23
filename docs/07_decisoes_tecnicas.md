# 07 - Decisoes Tecnicas

## DT-001 - Plataforma Inicial de Deploy

- Data: 2026-04-23
- Status: Aprovada
- Decisao: adotar `Vercel + Render` como plataforma inicial de producao.
- Escopo:
  - Frontend em Vercel.
  - Backend FastAPI em Render Web Service.
  - Banco PostgreSQL em Render.
- Motivo:
  - Melhor equilibrio entre custo, simplicidade operacional e velocidade para MVP.
- Consequencias:
  - Evita setup inicial mais pesado de infraestrutura em nuvem tradicional.
  - Exige disciplina de variaveis de ambiente, CORS e backup de banco.
