from fastapi import APIRouter
from app.schemas.gabinete import GabineteRequest, GabineteResponse
from app.services.calculos_gabinete import calcular_gabinete

router = APIRouter(prefix="/api/v1/gabinete", tags=["gabinete"])


@router.post("", response_model=GabineteResponse)
def calcular_gabinete_endpoint(payload: GabineteRequest) -> GabineteResponse:
    return calcular_gabinete(payload)
