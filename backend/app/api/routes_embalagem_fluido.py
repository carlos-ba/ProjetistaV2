from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.embalagem_fluido import EmbalagemFluido
from app.schemas.embalagem_fluido import EmbalagemFluido as EmbalagemFluidoSchema

router = APIRouter(prefix="/api/v1", tags=["embalagem_fluido"])


@router.get("/embalagem-fluido", response_model=List[EmbalagemFluidoSchema])
async def listar_embalagens_fluido(db: AsyncSession = Depends(get_db)):
    """Catálogo de tamanhos de embalagem descartável por fluido (Card 6)."""
    rows = (await db.execute(select(EmbalagemFluido).order_by(EmbalagemFluido.fluido, EmbalagemFluido.peso_kg))).scalars().all()
    return rows
