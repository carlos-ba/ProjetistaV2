# Backend — FastAPI

API REST do ProjetistaV2.

## Estrutura

```
app/
  main.py              Ponto de entrada, registro de routers
  api/
    routes_auth.py     Autenticação JWT
    routes_catalogo.py Equipamentos, fabricantes, categorias
    routes_calculo.py  Cálculo de carga térmica
    routes_selecao.py  Seleção de equipamentos por capacidade
    routes_tubulacao.py Dimensionamento de tubulação
    routes_projeto.py  CRUD de projetos salvos
    routes_cotacao.py  Fornecedores, cotações, importação de planilha
    routes_proposta.py Comparativo de fornecedores e proposta comercial
    routes_seed.py     Importação de dados do catálogo
  models/              SQLAlchemy ORM
  schemas/             Pydantic (entrada/saída)
  services/
    auth.py            JWT, hash de senha
    selecao_equipamentos.py  Interpolação de capacidade
    cotacao_excel.py   Geração da planilha Excel protegida
    cotacao_import.py  Parser da planilha devolvida pelo fornecedor
  database/
    session.py         AsyncSession + engine psycopg3
alembic/
  versions/            Migrations 0001→0009
```

## Execução Local

```powershell
# Na raiz do repositório
& ".venv\Scripts\python.exe" run.py
```

> **Importante:** usar `run.py`, não `uvicorn` direto. No Windows, o psycopg3 requer `WindowsSelectorEventLoopPolicy` que o `run.py` configura antes de iniciar o servidor.

## Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL de conexão PostgreSQL |
| `SECRET_KEY` | Chave JWT |
| `ALLOWED_ORIGINS` | CORS — origens permitidas |

## Deploy (Render)

Start command:
```
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

As migrations rodam automaticamente a cada deploy.
