from pydantic import BaseModel


class GabineteRequest(BaseModel):
    comprimento: float
    largura: float
    altura: float
    largura_painel: float
    espessura_mm: float = 100.0
    nucleo: str = "PUR"
    tipo_piso: str = "nenhum"
    espessura_concreto_cm: float = 0.0


class ItemCorte(BaseModel):
    item: str
    quantidade: int
    comprimento: float
    area_total: float
    descricao: str


class MaterialExtra(BaseModel):
    item: str
    qtd: str
    detalhe: str


class GabineteResponse(BaseModel):
    lista_corte: list[ItemCorte]
    materiais_extras: list[MaterialExtra]
    nucleo_selecionado: str
    espessura_considerada: str
    altura_util_calculada: float
    perda_altura: float
