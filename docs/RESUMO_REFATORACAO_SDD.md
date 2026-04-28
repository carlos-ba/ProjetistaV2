# Resumo de Refatoração com Premissas SDD

Este documento é um handoff para continuidade da refatoração em outro projeto, com foco em código limpo, separação de responsabilidades e evolução segura.

## 1) Contexto Atual

- Stack atual:
  - Backend: Django + DRF (`backend/`)
  - Frontend: React + Vite (`frontend/`)
- Domínio principal:
  - Dimensionamento de câmara fria
  - Cálculo de carga térmica
  - Seleção de equipamentos/componentes
  - Geração de orçamento e DXF
  - Persistência de projetos do usuário

## 2) Diagnóstico do Código (Estado Atual)

### Backend

- O arquivo [views.py](/C:/Users/carlo/PycharmProjects/projetista_frigorifico/backend/produtos/views.py) concentra responsabilidades demais:
  - regras de negócio,
  - parsing/validação de entrada,
  - orquestração de fluxo,
  - integração com recursos externos.
- Existem regras de negócio implementadas direto em endpoints, dificultando teste unitário puro.
- Seleção inteligente está parcialmente separada em [selecao.py](/C:/Users/carlo/PycharmProjects/projetista_frigorifico/backend/produtos/selecao.py), mas ainda acoplada a ORM e sem contratos explícitos.
- Modelos em [models.py](/C:/Users/carlo/PycharmProjects/projetista_frigorifico/backend/produtos/models.py) incluem dados de catálogo e operação no mesmo módulo; crescimento tende a aumentar acoplamento.

### Frontend

- O [App.jsx](/C:/Users/carlo/PycharmProjects/projetista_frigorifico/frontend/src/App.jsx) está como “orquestrador monolítico”:
  - muitos estados locais,
  - regras de fluxo por passo,
  - persistência de projeto e navegação de histórico no mesmo componente.
- Fluxo de negócio está acoplado à UI em vários pontos (scroll, alert, prompt, decisão de passo).
- API client em [api.js](/C:/Users/carlo/PycharmProjects/projetista_frigorifico/frontend/src/api.js) está funcional, mas o refresh token usa `axios.post('/api/auth/token/refresh/')` sem garantir `baseURL` consistente em todos os cenários.

## 3) Diretrizes SDD para o Novo Projeto

- S: Separar responsabilidades por camada (API, aplicação, domínio, infraestrutura).
- D: Definir contratos explícitos (DTOs, interfaces, schemas) para entrada/saída.
- D: Dirigir a evolução por domínio (use cases), não por framework.

## 4) Arquitetura Alvo (Sugestão Pragmática)

### Backend (Clean-ish + DDD leve)

- `domain/`
  - entidades de negócio (sem dependência de Django/DRF)
  - regras puras: cálculo gabinete, carga térmica, seleção
- `application/`
  - casos de uso: `calcular_gabinete`, `calcular_carga`, `selecionar_equipamento`, `montar_orcamento`
  - DTOs de entrada/saída
- `infrastructure/`
  - repositórios Django ORM
  - integrações (OpenAI, geração de arquivos)
- `interfaces/api/`
  - views/controllers DRF finos (somente adaptar HTTP <-> caso de uso)

### Frontend (Feature-first)

- `features/projeto/`
- `features/gabinete/`
- `features/carga-termica/`
- `features/selecao/`
- `features/orcamento/`
- `shared/api`, `shared/ui`, `shared/utils`

Com isso, `App.jsx` vira apenas composição de layout/rotas.

## 5) Backlog de Refatoração por Fases

### Fase 1 (ganho rápido)

- Extrair regras matemáticas de `views.py` para serviços puros.
- Criar schemas de request/response para cada endpoint crítico.
- Reduzir `App.jsx` movendo estado por feature (custom hooks ou context por módulo).

### Fase 2 (estrutura)

- Introduzir camada `application` com casos de uso.
- Criar repositórios para acesso a `Equipamento/Performance` (evitar ORM direto em regra).
- Padronizar erros de negócio (ex.: capacidade fora de faixa, input inconsistente).

### Fase 3 (qualidade)

- Testes unitários para regras puras (sem banco).
- Testes de integração para endpoints críticos.
- Testes E2E do fluxo principal (gabinete -> carga -> seleção -> orçamento -> salvar projeto).

## 6) Critérios de Pronto (Definition of Done)

- Cada endpoint com no máximo:
  - validação de entrada,
  - chamada de 1 caso de uso,
  - serialização da resposta.
- Regra de negócio sem import de `rest_framework`/`django.http`.
- Cobertura mínima dos casos críticos:
  - cálculo de carga,
  - seleção de equipamento por interpolação,
  - compatibilidade de componentes de fluxo.
- Frontend com estado dividido por feature e sem regra de domínio em componente de layout.

## 7) Riscos e Cuidados

- Refatorar seleção de equipamentos sem baseline pode alterar resultado de dimensionamento.
- Mudanças em payload de API quebram frontend se não houver versão/adapter.
- Cálculos térmicos exigem testes de regressão com exemplos reais já validados pela engenharia.

## 8) Estratégia de Migração para Outro Projeto

1. Copiar primeiro as regras puras e seus testes.
2. Criar API fina apenas para casos de uso já testados.
3. Migrar frontend por feature, mantendo um fluxo funcional de ponta a ponta a cada etapa.
4. Só depois portar integrações secundárias (DXF, IA, importadores de planilha).

## 9) Meta Técnica de Curto Prazo

Entregar um primeiro corte com:

- cálculo de gabinete,
- cálculo de carga térmica,
- seleção inteligente,
- salvamento de projeto,

todos desacoplados de framework na camada de domínio/aplicação, com testes automatizados.
