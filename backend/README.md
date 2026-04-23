# Backend (FastAPI)

Base inicial do backend seguindo a visão geral do projeto V2.

## Estrutura

- `app/main.py`: ponto de entrada da API.
- `app/api`: organização de rotas.
- `app/core`: configurações e utilitários centrais.
- `app/models`: modelos de domínio/ORM.
- `app/schemas`: schemas de entrada e saída.
- `app/services`: regras de negócio.
- `app/database`: camada de acesso ao banco.
- `tests`: testes do backend.

## Execução local

1. Criar e ativar ambiente virtual (fora do versionamento).
2. Instalar dependências:

```bash
pip install -r requirements.txt
```

3. Subir API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
