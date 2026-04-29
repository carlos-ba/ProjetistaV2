from fastapi import APIRouter
from app.schemas.tubulacao import TubulacaoRequest, TubulacaoResponse
from app.services.calculos_tubulacao import calcular_tubulacao

router = APIRouter(prefix="/api/v1/tubulacao", tags=["tubulacao"])


@router.post("", response_model=TubulacaoResponse)
def calcular_tubulacao_endpoint(payload: TubulacaoRequest) -> TubulacaoResponse:
    return calcular_tubulacao(payload)
