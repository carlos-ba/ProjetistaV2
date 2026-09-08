from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.carga_fluido import estimar_carga_fluido

router = APIRouter(prefix="/api/v1", tags=["carga_fluido"])


class CargaFluidoRequest(BaseModel):
    fluido:                  str   = Field(...,  examples=["R404A"])
    volume_interno_evap_kg:  float | None = Field(None, description="Volume interno do evaporador em kg (catálogo) — estimativa antiga")
    volume_interno_uc_kg:    float | None = Field(None, description="Volume interno da unidade condensadora em kg (catálogo) — hoje raramente cadastrado")
    carga_refrigerante_evap_kg: float | None = Field(None, description="Carga de refrigerante já publicada pelo fabricante do evaporador (kg) — preferida a volume_interno_evap_kg quando presente")
    carga_refrigerante_uc_kg:   float | None = Field(None, description="Carga de refrigerante já publicada pelo fabricante da UC (kg) — preferida a volume_interno_uc_kg quando presente")
    bitola_liquido:          str   = Field(...,  examples=['1/2"'])
    comprimento_liquido_m:   float = Field(...,  gt=0)
    bitola_succao:           str   = Field(...,  examples=['7/8"'])
    comprimento_succao_m:    float = Field(...,  gt=0)


@router.post("/carga-fluido/estimar")
def estimar(req: CargaFluidoRequest):
    try:
        return estimar_carga_fluido(
            fluido=req.fluido,
            volume_interno_evap_kg=req.volume_interno_evap_kg,
            bitola_liquido=req.bitola_liquido,
            comprimento_liquido_m=req.comprimento_liquido_m,
            bitola_succao=req.bitola_succao,
            comprimento_succao_m=req.comprimento_succao_m,
            volume_interno_uc_kg=req.volume_interno_uc_kg,
            carga_refrigerante_evap_kg=req.carga_refrigerante_evap_kg,
            carga_refrigerante_uc_kg=req.carga_refrigerante_uc_kg,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
