from pydantic import BaseModel


class TubulacaoRequest(BaseModel):
    capacidade_real: float
    distancia: float = 5.0
    temp_evap: float = -10.0
    alta_eficiencia: bool = True
    fluido: str = "R22"
    delta_t_selecionado: float = 6.0


class ItemTubulacao(BaseModel):
    item: str
    quantidade: int
    unidade: str
    detalhe: str


class TubulacaoResponse(BaseModel):
    diametro_liquido: str
    diametro_succao: str
    distancia_considerada: float
    temp_evap_calculada: float
    lista_materiais: list[ItemTubulacao]
