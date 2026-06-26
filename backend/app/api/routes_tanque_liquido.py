from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.tanque_liquido import selecionar_tanque_liquido

router = APIRouter(prefix="/api/v1", tags=["tanque_liquido"])


class TanqueLiquidoRequest(BaseModel):
    fluido:         str   = Field(..., examples=["R404A"])
    carga_total_kg: float = Field(..., gt=0, description="Carga total de fluido do sistema em kg")


@router.post("/tanque-liquido/selecionar")
def selecionar(req: TanqueLiquidoRequest):
    try:
        return selecionar_tanque_liquido(
            fluido=req.fluido,
            carga_total_kg=req.carga_total_kg,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
