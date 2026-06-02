from pydantic import BaseModel


class TubulacaoRequest(BaseModel):
    capacidade_real: float
    distancia: float = 5.0
    temp_evap: float = -10.0
    alta_eficiencia: bool = True
    fluido: str = "R22"
    delta_t_selecionado: float = 6.0
    padrao_isolamento: str = "H"       # D | F | H | M | R | T
    isolar_liquido: bool = False        # incluir isolamento na linha de líquido


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
    padrao_isolamento_usado: str
    sugestao_padrao: str               # padrão sugerido pela regra técnica
    lista_materiais: list[ItemTubulacao]


class SugestaoIsolamentoResponse(BaseModel):
    padrao: str
    descricao: str
    faixa_espessura: str
    justificativa: str
