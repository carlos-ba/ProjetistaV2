# CHECKPOINT DESENVOLVIMENTO - 2026-04-28

## Objetivo da sessão
Adaptar o projeto `ProjetistaV2` para diretrizes SDD e iniciar a Fase 1 de migração de lógica do projeto antigo (`projetista_frigorifico`) para a nova arquitetura.

## O que foi concluído hoje

### 1) Documentação SDD mínima estruturada
Foram preenchidos os documentos-base que estavam como placeholder:
- `docs/02_arquitetura.md`
- `docs/03_banco_de_dados.md`
- `docs/04_api.md`
- `docs/05_frontend.md`

Resultado: arquitetura, dados, contrato de API e diretriz frontend agora têm base concreta para implementação.

### 2) Commit de documentação realizado
Commit criado:
- Hash: `f62f02e`
- Mensagem: `docs(sdd): definir arquitetura, dados, API e frontend MVP`

Observação: o arquivo `docs/RESUMO_REFATORACAO_SDD.md` entrou no mesmo commit pois já estava staged.

### 3) Análise do projeto antigo para migração
Projeto analisado:
- `C:\Users\carlo\PycharmProjects\projetista_frigorifico`

Arquivos-chave identificados para migração:
- Backend: `backend/produtos/views.py`, `backend/produtos/selecao.py`, `backend/produtos/models.py`, `backend/produtos/serializers.py`
- Frontend: `frontend/src/App.jsx`, `frontend/src/api.js`, `frontend/src/components/*`

Riscos críticos encontrados no antigo:
- `views.py` com acoplamento alto (HTTP + regra + integração externa)
- Chave OpenAI hardcoded em `backend/produtos/views.py` (não migrar)
- `frontend/src/api.js` faz refresh token com `axios.post` fora da instância principal (baseURL inconsistente)
- `App.jsx` monolítico

### 4) Fase 1 iniciada no backend do projeto novo (SDD)
Implementado em `ProjetistaV2/backend/app`:

Novos arquivos:
- `api/routes_health.py` -> endpoint `GET /health`
- `api/routes_calculos.py` -> endpoint `POST /api/v1/calculos`
- `schemas/calculo.py` -> contratos Request/Response
- `services/calculos.py` -> lógica de cálculo e seleção com interpolação

Arquivos alterados:
- `main.py` -> inclusão de rotas
- `api/__init__.py`
- `schemas/__init__.py`
- `services/__init__.py`

## Estado atual do git (importante)
Ainda existem alterações não commitadas referentes à Fase 1:
- `backend/app/main.py`
- `backend/app/api/__init__.py`
- `backend/app/schemas/__init__.py`
- `backend/app/services/__init__.py`
- `backend/app/api/routes_health.py` (novo)
- `backend/app/api/routes_calculos.py` (novo)
- `backend/app/schemas/calculo.py` (novo)
- `backend/app/services/calculos.py` (novo)

Também existem alterações prévias fora deste escopo:
- `docs/01_requisitos.md` (modificado)
- `docs/08_status_atual.md` (modificado)
- `.claude/` (não rastreado)

## Próximo passo recomendado (amanhã)
1. Validar runtime da Fase 1:
- subir backend e testar `GET /health`
- testar `POST /api/v1/calculos` com payload mínimo

2. Criar testes automáticos (Fase 1.1):
- teste de `/health`
- teste de contrato de `/api/v1/calculos`
- teste unitário para interpolação/seleção em `services/calculos.py`

3. Após validar, criar commit da Fase 1 backend:
Sugestão de mensagem:
- `feat(backend): implementar fase 1 sdd com health e calculos`

## Payload exemplo para testar `/api/v1/calculos`
```json
{
  "projeto_id": "11111111-1111-1111-1111-111111111111",
  "entrada": {
    "largura": 2.4,
    "altura": 2.2,
    "comprimento": 3.0
  },
  "temp_evaporacao": -10,
  "fluido": "R404A",
  "tipo_equipamento": "Unidade Condensadora",
  "equipamentos": [
    {
      "id": "eq-1",
      "modelo": "Modelo X",
      "fabricante": "Fab A",
      "categoria": "Unidade Condensadora",
      "fluido": "R404A",
      "vazao_ar_m3h": 2500,
      "preco": 10000,
      "pontos": [
        {"temp_evaporacao": -15, "capacidade": 13000},
        {"temp_evaporacao": -10, "capacidade": 15000},
        {"temp_evaporacao": -5, "capacidade": 17000}
      ]
    }
  ]
}
```

## Arquivo de referência desta sessão
- `docs/CHECKPOINT_2026-04-28_DESENVOLVIMENTO_SDD.md`
