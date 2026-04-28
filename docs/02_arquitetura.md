# 02 - Arquitetura

Documento de arquitetura do MVP com foco em adaptacao ao modelo SDD.

## 1. Objetivo Arquitetural

- Separar responsabilidades por camada.
- Definir contratos explicitos entre frontend e backend.
- Permitir evolucao incremental sem acoplamento forte a framework.

## 2. Visao de Containers (alto nivel)

- Frontend (Vercel): interface web e consumo da API.
- Backend FastAPI (Render): regras de negocio e orquestracao de casos de uso.
- PostgreSQL (Render): persistencia de dados de dominio.

## 3. Estrutura Alvo do Backend (SDD pragmatica)

Base atual:
- `app/main.py`
- `app/api/`
- `app/core/`
- `app/models/`
- `app/schemas/`
- `app/services/`
- `app/database/`

Responsabilidades por camada:
- `api`: endpoints HTTP finos (validar entrada, chamar caso de uso, devolver resposta).
- `schemas`: contratos de request/response (DTOs da API).
- `services`: regras de negocio e casos de uso (sem dependencia de HTTP).
- `models`: entidades ORM e mapeamento de persistencia.
- `database`: sessao, engine e repositorios de dados.
- `core`: configuracoes, logging e utilitarios transversais.

## 4. Fluxo Base de Requisicao

1. Frontend envia requisicao HTTP para endpoint FastAPI.
2. Endpoint valida payload com schema.
3. Endpoint chama servico/caso de uso.
4. Servico aplica regra de negocio e usa repositorio.
5. Repositorio persiste/consulta no PostgreSQL.
6. Endpoint retorna resposta tipada por schema.

## 5. Principios de Implementacao

- Endpoint nao implementa regra de negocio complexa.
- Regra de negocio nao depende de objetos HTTP.
- Contratos da API versionados no proprio documento de API.
- Mudanca estrutural relevante deve gerar registro em `docs/07_decisoes_tecnicas.md`.

## 6. Premissas de Deploy

- Frontend: Vercel.
- Backend: Render Web Service.
- Banco: Render PostgreSQL.
- Persistencia somente em banco de dados (sem dependencia de filesystem local).
