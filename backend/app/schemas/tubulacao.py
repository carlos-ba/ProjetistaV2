from typing import Optional
from pydantic import BaseModel


class TubulacaoRequest(BaseModel):
    capacidade_real: float
    distancia: float = 5.0
    temp_evap: float = -10.0
    alta_eficiencia: bool = True
    fluido: str = "R22"
    delta_t_selecionado: float = 6.0
    padrao_isolamento: str = "H"
    isolar_liquido: bool = False
    num_circuitos: int = 1
    parede_liquido: str = "fina"    # "fina" (0.79mm) ou "grossa" (1.59mm)
    parede_succao: str = "fina"     # "fina" (0.79mm) ou "grossa" (1.59mm)


class ItemTubulacao(BaseModel):
    item: str
    quantidade: int
    unidade: str
    detalhe: str
    quantidade_kg: Optional[float] = None   # peso total em kg (só para tubos de cobre)
    peso_por_metro: Optional[float] = None  # kg/m da bitola+parede selecionada


class TubulacaoResponse(BaseModel):
    diametro_liquido: str
    diametro_succao: str
    distancia_considerada: float
    temp_evap_calculada: float
    padrao_isolamento_usado: str
    sugestao_padrao: str
    lista_materiais: list[ItemTubulacao]


class SugestaoIsolamentoResponse(BaseModel):
    padrao: str
    descricao: str
    faixa_espessura: str
    justificativa: str


class PesoTuboCobre(BaseModel):
    bitola_pol: str
    diametro_mm: float
    parede_fina: Optional[float]
    parede_grossa: Optional[float]

    class Config:
        from_attributes = True
