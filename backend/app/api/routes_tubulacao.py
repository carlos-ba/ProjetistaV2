from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.tubulacao import TubulacaoRequest, TubulacaoResponse, SugestaoIsolamentoResponse, PesoTuboCobre as PesoTuboCobresSchema
from app.models.peso_tubo_cobre import PesoTuboCobre
from app.services.calculos_tubulacao import calcular_tubulacao, sugerir_padrao, _INFO_PADRAO

router = APIRouter(prefix="/api/v1/tubulacao", tags=["tubulacao"])


@router.post("", response_model=TubulacaoResponse)
async def calcular_tubulacao_endpoint(
    payload: TubulacaoRequest,
    db: AsyncSession = Depends(get_db),
) -> TubulacaoResponse:
    return await calcular_tubulacao(payload, db)


@router.get("/peso-tubo-cobre", response_model=List[PesoTuboCobresSchema])
async def listar_pesos_tubo(db: AsyncSession = Depends(get_db)):
    """Retorna a tabela de peso por metro dos tubos de cobre (Forming Tubing)."""
    rows = (await db.execute(select(PesoTuboCobre).order_by(PesoTuboCobre.diametro_mm))).scalars().all()
    return rows


@router.get("/sugestao-isolamento", response_model=SugestaoIsolamentoResponse)
def sugestao_isolamento(temp_evap: float = Query(..., description="Temperatura de evaporação °C")):
    """Retorna o padrão de isolamento sugerido para a T.Evap informada."""
    padrao, justificativa = sugerir_padrao(temp_evap)
    faixa, descricao = _INFO_PADRAO[padrao]
    return SugestaoIsolamentoResponse(
        padrao=padrao,
        descricao=descricao,
        faixa_espessura=faixa,
        justificativa=justificativa,
    )
