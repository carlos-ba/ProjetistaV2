from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.orcamento import OrcamentoRequest, OrcamentoResponse
from app.services.orcamento import gerar_orcamento

router = APIRouter(prefix="/api/v1/orcamento", tags=["orcamento"])


@router.post("", response_model=OrcamentoResponse)
async def gerar_orcamento_endpoint(
    payload: OrcamentoRequest,
    db: AsyncSession = Depends(get_db),
) -> OrcamentoResponse:
    return await gerar_orcamento(payload, db)
