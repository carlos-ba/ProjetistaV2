from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.componente import ComponenteFluxoRequest, ComponenteSelecionado
from app.services.componentes_fluxo import selecionar_componentes_fluxo

router = APIRouter(prefix="/api/v1/componentes", tags=["componentes"])


@router.post("", response_model=list[ComponenteSelecionado])
async def selecionar_componentes_endpoint(
    payload: ComponenteFluxoRequest,
    db: AsyncSession = Depends(get_db),
) -> list[ComponenteSelecionado]:
    return await selecionar_componentes_fluxo(payload, db)
