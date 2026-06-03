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
    # Conexões
    num_curvas_90: int | None = None    # None = automático por distância
    incluir_sifao: bool = True          # sifão + contra-sifão na sucção (saída evap)


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
    sugestao_padrao: str
    curvas_90_usadas: int              # qtde de curvas 90° (auto ou informado)
    origem_curvas: str                 # "automático" ou "informado pelo técnico"
    lista_materiais: list[ItemTubulacao]


class SugestaoIsolamentoResponse(BaseModel):
    padrao: str
    descricao: str
    faixa_espessura: str
    justificativa: str
