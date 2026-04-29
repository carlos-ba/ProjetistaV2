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

  ---

  ## DT-002 - Stack de Persistência e Padrão de Acesso a Dados

  - Data: 2026-04-29
  - Status: Aprovada
  - Decisão: Adotar `SQLAlchemy 2.0 (Async)` + `Psycopg 3` + `Alembic`.
  - Motivo:
    - SQLAlchemy 2.0 oferece suporte nativo e robusto para Python assíncrono.
    - Psycopg 3 é a nova geração do driver, com melhor performance e suporte a tipos modernos.
    - Alembic permite controle seguro do esquema do banco de dados via migrações.
  - Consequências:
    - Necessidade de gerenciar sessões assíncronas no FastAPI (`AsyncSession`).
    - Configuração específica de loop de eventos (`WindowsSelectorEventLoopPolicy`) para desenvolvimento local em Windows.

  ## DT-003 - Arquitetura de Camadas (SDD)

  - Data: 2026-04-29
  - Status: Aprovada
  - Decisão: Seguir rigorosamente a separação entre `models`, `schemas`, `services` e `api`.
  - Motivo:
    - Facilita o teste unitário de lógica pura (serviços) sem dependência de frameworks.
    - Garante contratos explícitos de entrada/saída (schemas) desacoplados do banco (models).
    - Alinhamento com as premissas SDD (Separation, Definition, Direction) para evitar o acoplamento do projeto V1.
