from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.schemas.auth import HealthResponse
from app.database.session import engine

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/health/db")
async def healthcheck_db():
    """Diagnóstico de conexão com o banco — remover após resolver o problema."""
    result = {"status": "ok", "db": "connected", "tables": {}}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})

    # Verificar se as tabelas existem
    for table in ["fabricante", "equipamento", "material", "usuario"]:
        try:
            async with engine.connect() as conn:
                r = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                result["tables"][table] = r.scalar()
        except Exception as e:
            result["tables"][table] = f"ERRO: {str(e)[:80]}"

    return result
