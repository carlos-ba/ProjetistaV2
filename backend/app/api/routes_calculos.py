from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.calculo import CalculoRequest, CalculoResponse
from app.services.calculos import processar_e_salvar_calculo

router = APIRouter(prefix="/api/v1/calculos", tags=["calculos"])


@router.post("", response_model=CalculoResponse, status_code=201)
async def criar_calculo(
    payload: CalculoRequest, 
    db: AsyncSession = Depends(get_db)
) -> CalculoResponse:
    return await processar_e_salvar_calculo(db=db, payload=payload)
