from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.cavalete import analisar_cavalete

router = APIRouter(prefix="/api/v1", tags=["cavalete"])


class CavaleteRequest(BaseModel):
    # Equipamentos
    condensadora_cx_liquido: str = Field(..., examples=['3/8"'])
    condensadora_cx_succao:  str = Field(..., examples=['5/8"'])
    evaporador_cx_liquido:   str = Field(..., examples=['1/2"'])
    evaporador_cx_succao:    str = Field(..., examples=['7/8"'])
    # Linhas (Card 4)
    diametro_liquido: str = Field(..., examples=['1/2"'])
    diametro_succao:  str = Field(..., examples=['7/8"'])
    # Componentes do cavalete
    filtro_conexao:    str = Field(..., examples=['1/2"'])
    filtro_tipo:       str = Field(..., examples=['solda'])   # 'solda' | 'rosca'
    solenoide_conexao: str = Field(..., examples=['1/2"'])
    visor_conexao:     str = Field(..., examples=['1/2"'])
    visor_tipo:        str = Field(..., examples=['solda'])   # 'solda' | 'rosca'
    vet_entrada:       str = Field('3/8"')
    vet_saida:         str = Field('1/2"')
    # Comprimentos
    comprimento_liquido_m: float = Field(..., gt=0)
    comprimento_succao_m:  float = Field(..., gt=0)
    # Trechos do cavalete (Configurações)
    trecho_vet_evap_m:    float = Field(0.5)
    trecho_evap_sifao_m:  float = Field(0.5)
    trecho_subida_m:      float = Field(1.0)
    trecho_sifao_gbc_m:   float = Field(0.5)
    # Tanque (opcional)
    tanque_conexao: str | None = None
    # Flags de inclusão (Configurações)
    incluir_filtro:      bool = Field(True)
    incluir_visor:       bool = Field(True)
    incluir_gbc_entrada: bool = Field(True)
    incluir_gbc_saida:   bool = Field(True)


@router.post("/cavalete/analisar")
def analisar(req: CavaleteRequest):
    try:
        return analisar_cavalete(**req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
