import asyncio
import sys

# Windows: psycopg async requer SelectorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(
    title="Projetista V2 API",
    version="0.2.0",
    description="API de dimensionamento frigorífico — FastAPI + PostgreSQL.",
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
