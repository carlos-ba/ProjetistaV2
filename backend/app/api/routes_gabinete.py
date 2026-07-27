from fastapi import APIRouter
from fastapi.responses import Response

from app.schemas.gabinete import GabineteRequest, GabineteResponse, GabineteDXFRequest
from app.services.calculos_gabinete import calcular_gabinete
from app.services.dxf_gabinete import gerar_dxf_gabinete

router = APIRouter(prefix="/api/v1/gabinete", tags=["gabinete"])


@router.post("", response_model=GabineteResponse)
def calcular_gabinete_endpoint(payload: GabineteRequest) -> GabineteResponse:
    return calcular_gabinete(payload)


@router.post("/dxf/")
def gerar_dxf_endpoint(payload: GabineteDXFRequest) -> Response:
    dxf = gerar_dxf_gabinete(payload)
    return Response(
        content=dxf,
        media_type="application/dxf",
        headers={"Content-Disposition": 'attachment; filename="projeto_camara.dxf"'},
    )
