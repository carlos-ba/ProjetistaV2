from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.selecao import SelecaoRequest, EquipamentoSelecionado
from app.services.selecao_equipamentos import selecionar_equipamentos_db

router = APIRouter(prefix="/api/v1/selecao", tags=["selecao"])


@router.post("", response_model=list[EquipamentoSelecionado])
async def selecao_inteligente(
    payload: SelecaoRequest,
    db: AsyncSession = Depends(get_db),
) -> list[EquipamentoSelecionado]:
    return await selecionar_equipamentos_db(payload, db)
