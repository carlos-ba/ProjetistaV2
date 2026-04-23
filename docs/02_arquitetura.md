# 02 - Arquitetura

Documento de arquitetura em evolucao do sistema.

## Premissa Atual de Hospedagem

- Frontend: Vercel
- Backend: Render Web Service
- Banco de dados: Render PostgreSQL

## Observacoes

- Backend e frontend permanecem separados.
- Persistencia de dados fica no banco, nao no filesystem do backend.
- Ajustes de arquitetura devem ser registrados em `docs/07_decisoes_tecnicas.md`.
