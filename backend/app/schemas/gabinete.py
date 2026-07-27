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
    piso_rebaixado: bool = False   # convencional rebaixado (nivelado, sem degrau)


class GabineteDXFRequest(BaseModel):
    """Payload do botão 'Baixar Projeto CAD (.DXF)' do Card 1 (dimensões em metros)."""
    comprimento: float
    largura: float
    altura: float
    largura_painel: float = 1.1
    espessura: float = 100.0   # mm


class ItemCorte(BaseModel):
    item: str
    quantidade: int
    comprimento: float
    area_total: float
    descricao: str
    tipo_item: str | None = None


class MaterialExtra(BaseModel):
    item: str
    qtd: str
    detalhe: str
    tipo_item: str | None = None


class GabineteResponse(BaseModel):
    lista_corte: list[ItemCorte]
    materiais_extras: list[MaterialExtra]
    nucleo_selecionado: str
    espessura_considerada: str
    altura_util_calculada: float
    perda_altura: float
