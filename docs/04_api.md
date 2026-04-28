# 04 - API

Contrato minimo de API para validar a adaptacao SDD no MVP.

## 1. Padroes Gerais

- Formato: JSON.
- Prefixo sugerido: `/api/v1`.
- Timezone: UTC em campos de data/hora.
- Erros padronizados com `code`, `message`, `details`.

## 2. Endpoint de Health

### GET `/health`

Resposta `200`:

```json
{
  "status": "ok"
}
```

Objetivo:
- validar disponibilidade do servico.

## 3. Endpoint de Calculo (MVP de contrato)

### POST `/api/v1/calculos`

Request:

```json
{
  "projeto_id": "uuid",
  "entrada": {
    "largura": 2.4,
    "altura": 2.2,
    "comprimento": 3.0
  }
}
```

Regras basicas:
- `projeto_id` obrigatorio e formato UUID.
- `entrada` obrigatoria.
- dimensoes devem ser numericas e maiores que zero.

Resposta `201`:

```json
{
  "id": "uuid",
  "projeto_id": "uuid",
  "resultado": {
    "volume": 15.84
  },
  "versao_regra": "v1",
  "created_at": "2026-04-28T12:00:00Z"
}
```

Resposta `422` (erro de validacao):

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Payload invalido",
  "details": {
    "entrada.largura": "deve ser maior que zero"
  }
}
```

## 4. Endpoint de Projeto (MVP de cadastro)

### POST `/api/v1/projetos`

Request:

```json
{
  "nome": "Projeto teste SDD"
}
```

Resposta `201`:

```json
{
  "id": "uuid",
  "nome": "Projeto teste SDD",
  "status": "rascunho",
  "created_at": "2026-04-28T12:00:00Z"
}
```
