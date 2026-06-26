import asyncio
import sys

# Windows: psycopg async requer SelectorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command


def _run_migrations():
    import os
    import logging
    try:
        ini = os.path.join(os.path.dirname(__file__), '..', 'alembic.ini')
        cfg = AlembicConfig(os.path.abspath(ini))
        alembic_command.upgrade(cfg, 'head')
    except Exception as exc:
        logging.getLogger(__name__).error("Falha ao rodar migrations no startup: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Roda em thread separada: env.py usa asyncio.run() que não pode ser
    # chamado dentro de um loop já ativo (o loop do FastAPI/uvicorn)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_migrations)
    yield

from app.core.config import settings
from app.api.routes_auth import router as auth_router
from app.api.routes_health import router as health_router
from app.api.routes_projetos import router as projetos_router
from app.api.routes_calculos import router as calculos_router
from app.api.routes_gabinete import router as gabinete_router
from app.api.routes_carga_termica import router as carga_termica_router
from app.api.routes_selecao import router as selecao_router
from app.api.routes_tubulacao import router as tubulacao_router
from app.api.routes_orcamento import router as orcamento_router
from app.api.routes_componentes import router as componentes_router
from app.api.routes_catalogo import router as catalogo_router
from app.api.routes_seed import router as seed_router
from app.api.routes_cotacao import router as cotacao_router
from app.api.routes_proposta import router as proposta_router
from app.api.routes_solenoide import router as solenoide_router
from app.api.routes_acessorios import router as acessorios_router
from app.api.routes_carga_fluido import router as carga_fluido_router
from app.api.routes_tanque_liquido import router as tanque_liquido_router
from app.api.routes_cavalete import router as cavalete_router
from app.api.routes_configuracoes import router as configuracoes_router

app = FastAPI(
    title="Projetista V2 API",
    version="0.2.0",
    description="API de dimensionamento frigorífico — FastAPI + PostgreSQL.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(projetos_router)
app.include_router(calculos_router)
app.include_router(gabinete_router)
app.include_router(carga_termica_router)
app.include_router(selecao_router)
app.include_router(tubulacao_router)
app.include_router(orcamento_router)
app.include_router(componentes_router)
app.include_router(catalogo_router)
app.include_router(seed_router)
app.include_router(cotacao_router)
app.include_router(proposta_router)
app.include_router(solenoide_router)
app.include_router(acessorios_router)
app.include_router(carga_fluido_router)
app.include_router(tanque_liquido_router)
app.include_router(cavalete_router)
app.include_router(configuracoes_router)
