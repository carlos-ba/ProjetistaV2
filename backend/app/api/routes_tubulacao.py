from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.tubulacao import TubulacaoRequest, TubulacaoResponse, SugestaoIsolamentoResponse
from app.services.calculos_tubulacao import calcular_tubulacao, sugerir_padrao, _INFO_PADRAO

router = APIRouter(prefix="/api/v1/tubulacao", tags=["tubulacao"])


@router.post("", response_model=TubulacaoResponse)
async def calcular_tubulacao_endpoint(
    payload: TubulacaoRequest,
    db: AsyncSession = Depends(get_db),
) -> TubulacaoResponse:
    return await calcular_tubulacao(payload, db)


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
