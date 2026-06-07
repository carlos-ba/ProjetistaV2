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
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e), "type": type(e).__name__},
        )
