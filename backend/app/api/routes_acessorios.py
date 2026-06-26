from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.acessorios import selecionar_acessorios

router = APIRouter(prefix="/api/v1", tags=["acessorios"])


class AcessoriosSelecionarRequest(BaseModel):
    fluido:             str   = Field(..., examples=["R404A"])
    capacidade_kcalh:   float = Field(..., description="Carga térmica em kcal/h")
    tem_tanque_liquido: bool  = Field(True, description="True → DML; False → DMC")


@router.post("/acessorios/selecionar")
def selecionar(req: AcessoriosSelecionarRequest):
    try:
        return selecionar_acessorios(
            fluido=req.fluido,
            capacidade_kcalh=req.capacidade_kcalh,
            tem_tanque_liquido=req.tem_tanque_liquido,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
