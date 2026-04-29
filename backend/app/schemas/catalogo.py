from decimal import Decimal
from pydantic import BaseModel


class TipoProdutoTermicoOut(BaseModel):
    id: int
    nome: str

    model_config = {"from_attributes": True}


class PerfilProdutoTermicoOut(BaseModel):
    id: int
    nome: str
    tipo_id: int
    ponto_congelamento: Decimal
    calor_especifico_acima_congelamento: Decimal
    calor_latente_congelamento: Decimal
    calor_especifico_abaixo_congelamento: Decimal
    taxa_respiracao: Decimal | None
    temperatura_conservacao: Decimal | None
    umidade_relativa: Decimal | None
    teor_agua: Decimal | None

    model_config = {"from_attributes": True}


class CategoriaOut(BaseModel):
    id: int
    nome: str

    model_config = {"from_attributes": True}


class FabricanteOut(BaseModel):
    id: int
    nome: str

    model_config = {"from_attributes": True}


class UnidadeMedidaOut(BaseModel):
    id: int
    nome: str
    sigla: str

    model_config = {"from_attributes": True}


class MaterialOut(BaseModel):
    id: int
    nome: str
    custo: Decimal
    unidade_medida_id: int
    capacidade_nominal: float
    diametro_conexao: str | None

    model_config = {"from_attributes": True}


class EquipamentoOut(BaseModel):
    id: int
    modelo: str
    fabricante_id: int
    categoria_id: int
    custo: Decimal
    qtde_ventiladores: int
    diametro_ventilador_mm: int
    vazao_ar_m3h: int
    flecha_ar_m: int

    model_config = {"from_attributes": True}
