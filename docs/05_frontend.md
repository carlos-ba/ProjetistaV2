# 05 - Frontend

Diretrizes minimas de frontend para o teste de arquitetura SDD.

## 1. Objetivo do MVP

- Permitir criar projeto.
- Permitir enviar dados de entrada para calculo.
- Exibir resultado retornado pela API.

## 2. Estrutura Recomendada (feature-first)

- `src/features/projetos/`
- `src/features/calculos/`
- `src/shared/api/`
- `src/shared/ui/`
- `src/shared/utils/`

## 3. Fluxo Principal de Tela

1. Usuario cria projeto (nome).
2. Usuario preenche formulario de calculo.
3. Frontend chama `POST /api/v1/calculos`.
4. Frontend mostra resultado (`volume` no MVP).

## 4. Regras de Integracao

- `baseURL` da API deve vir de variavel de ambiente.
- Erros da API devem ser exibidos com mensagem clara.
- Tela nao deve conter regra de calculo de dominio; somente coleta dados e exibe resposta.

## 5. Critérios Minimos de Pronto

- Formulario com validacao basica de campos obrigatorios.
- Estados de `loading`, `success` e `error`.
- Componentes separados por feature (evitar componente monolitico).
