from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.gabinete import GabineteRequest, GabineteResponse, GabineteDXFRequest
from app.services.calculos_gabinete import calcular_gabinete
from app.services.kit_montagem import calcular_kit_montagem
from app.services.barreira_vapor import calcular_barreira_vapor
from app.services.dxf_gabinete import gerar_dxf_gabinete

router = APIRouter(prefix="/api/v1/gabinete", tags=["gabinete"])


@router.post("", response_model=GabineteResponse)
async def calcular_gabinete_endpoint(
    payload: GabineteRequest,
    db: AsyncSession = Depends(get_db),
) -> GabineteResponse:
    resultado = calcular_gabinete(payload)
    itens_kit, avisos_kit = await calcular_kit_montagem(
        db,
        comprimento=payload.comprimento,
        largura=payload.largura,
        comp_parede_m=resultado.comp_parede_m,
        espessura_painel_mm=payload.espessura_mm,
        area_total_paineis_m2=resultado.area_total_paineis_m2,
        largura_aba_padrao_mm=payload.largura_aba_padrao_mm,
        rendimento_selante_m_por_embalagem=payload.rendimento_selante_m_por_embalagem,
        fator_seguranca_selante=payload.fator_seguranca_selante,
        perfis_manuais=payload.perfis_manuais,
    )
    itens_barreira, avisos_barreira = await calcular_barreira_vapor(db, resultado.area_piso_m2)
    resultado.materiais_extras += itens_kit + itens_barreira
    resultado.avisos_kit_montagem = avisos_kit + avisos_barreira
    return resultado


@router.post("/dxf/")
def gerar_dxf_endpoint(payload: GabineteDXFRequest) -> Response:
    dxf = gerar_dxf_gabinete(payload)
    return Response(
        content=dxf,
        media_type="application/dxf",
        headers={"Content-Disposition": 'attachment; filename="projeto_camara.dxf"'},
    )
