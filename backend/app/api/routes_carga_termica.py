from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.carga_termica import CargaTermicaRequest, CargaTermicaResponse
from app.services.calculos_carga_termica import calcular_carga_termica

router = APIRouter(prefix="/api/v1/carga-termica", tags=["carga-termica"])


@router.post("", response_model=CargaTermicaResponse)
async def calcular_carga_termica_endpoint(
    payload: CargaTermicaRequest,
    db: AsyncSession = Depends(get_db),
) -> CargaTermicaResponse:
    return await calcular_carga_termica(payload, db)
