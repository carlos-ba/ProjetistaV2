from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class DimensoesEntrada(BaseModel):
    largura: float = Field(..., gt=0)
    altura: float = Field(..., gt=0)
    comprimento: float = Field(..., gt=0)


class PerformancePonto(BaseModel):
    temp_evaporacao: float
    capacidade: float = Field(..., gt=0)


class EquipamentoEntrada(BaseModel):
    id: str
    modelo: str
    fabricante: str
    categoria: str
    fluido: str
    vazao_ar_m3h: float = Field(0, ge=0)
    preco: float = Field(0, ge=0)
    pontos: list[PerformancePonto] = Field(default_factory=list)


class CalculoRequest(BaseModel):
    projeto_id: UUID
    entrada: DimensoesEntrada
    temp_evaporacao: float = -10
    temp_condensacao: float = 45
    fluido: str = "R404A"
    tipo_equipamento: str = "Unidade Condensadora"
    equipamentos: list[EquipamentoEntrada] = Field(default_factory=list)


class SelecaoEquipamento(BaseModel):
    id: str
    modelo: str
    fabricante: str
    capacidade_real: float
    vazao_ar: float
    preco: float
    diferenca: float
    percentual: float
    status: str


class CalculoResultado(BaseModel):
    volume: float
    carga_estimativa_kcalh: float
    selecao: list[SelecaoEquipamento] = Field(default_factory=list)


class CalculoResponse(BaseModel):
    id: UUID
    projeto_id: UUID
    resultado: CalculoResultado
    versao_regra: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


def build_response(projeto_id: UUID, resultado: CalculoResultado, versao_regra: str = "v1") -> CalculoResponse:
    return CalculoResponse(
        id=uuid4(),
        projeto_id=projeto_id,
        resultado=resultado,
        versao_regra=versao_regra,
        created_at=datetime.now(timezone.utc),
    )
