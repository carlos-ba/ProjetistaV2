# 09 - Proximos Passos

Este roteiro define a ordem de retomada para a proxima sessao.

## 1. Requisitos e Escopo

1. Detalhar requisitos funcionais em `docs/01_requisitos.md`.
2. Definir fluxo do usuario para calculo e geracao da lista de pecas.
3. Definir regras de negocio minimas para o primeiro MVP.

## 2. Modelo de Dados

1. Definir entidades principais em `docs/03_banco_de_dados.md`.
2. Definir relacionamentos e campos obrigatorios.
3. Definir estrategia de versionamento de schema (migrations).

## 3. Backend MVP

1. Criar configuracao central de ambiente no backend.
2. Implementar endpoint de health (`/health`).
3. Implementar primeiro endpoint de calculo (entrada/saida).
4. Implementar persistencia inicial no PostgreSQL.
5. Adicionar testes de API para os endpoints iniciais.

## 4. Frontend MVP

1. Inicializar base real do frontend (React/Vite ou Next.js).
2. Criar tela inicial com formulario de entrada de dados.
3. Integrar chamada ao endpoint de calculo.
4. Exibir resultado e salvar para consulta futura.

## 5. Operacao e Qualidade

1. Adicionar logs estruturados no backend.
2. Definir padrao de tratamento de erros.
3. Revisar variaveis de ambiente e padroes de seguranca.
4. Atualizar documentacao de deploy conforme evolucao.

## 6. Regra de Trabalho para Retomada

1. Sempre iniciar com `git pull origin main`.
2. Implementar em pequenas entregas com commit por etapa.
3. Atualizar `docs/08_status_atual.md` ao final de cada sessao relevante.
