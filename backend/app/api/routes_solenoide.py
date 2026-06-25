from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.solenoide import selecionar_solenoide

router = APIRouter(prefix="/api/v1", tags=["solenoide"])


class SolenoideSelecionarRequest(BaseModel):
    fluido:        str   = Field(..., examples=["R404A"])
    te_c:          float = Field(..., description="Temperatura de evaporação (°C)")
    tc_c:          float = Field(..., description="Temperatura de condensação (°C)")
    capacidade_kw: float = Field(..., description="Capacidade necessária (kW)")
    dp_bar:        float = Field(0.10, description="ΔP admissível na válvula (bar)")


@router.post("/solenoide/selecionar")
def selecionar(req: SolenoideSelecionarRequest):
    try:
        return selecionar_solenoide(
            fluido=req.fluido,
            te=req.te_c,
            tc=req.tc_c,
            capacidade_kw=req.capacidade_kw,
            dp_bar=req.dp_bar,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
