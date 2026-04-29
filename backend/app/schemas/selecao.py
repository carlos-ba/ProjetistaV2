from pydantic import BaseModel


class SelecaoRequest(BaseModel):
    carga_termica_total: float
    temp_evaporacao: float = -10.0
    temp_condensacao: float = 45.0
    fluido: str = "R22"
    tipo: str = "Unidade Condensadora"


class EquipamentoSelecionado(BaseModel):
    id: int
    modelo: str
    fabricante: str
    capacidade_real: float
    vazao_ar: int
    preco: float
    diferenca: float
    percentual: float
    status: str
