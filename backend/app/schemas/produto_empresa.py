from pydantic import BaseModel, field_validator


class ProdutoEmpresaCreate(BaseModel):
    descricao: str
    codigo_interno: str | None = None
    unidade: str = "un"
    preco: float
    tipo_catalogo: str | None = None
    ref_global: int | None = None
    ativo: bool = True

    @field_validator("descricao")
    @classmethod
    def descricao_obrigatoria(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Descrição é obrigatória.")
        return v.strip()

    @field_validator("tipo_catalogo")
    @classmethod
    def tipo_catalogo_valido(cls, v: str | None) -> str | None:
        if v is not None and v not in ("material", "equipamento"):
            raise ValueError("tipo_catalogo deve ser 'material' ou 'equipamento'.")
        return v


class ProdutoEmpresaUpdate(BaseModel):
    descricao: str | None = None
    codigo_interno: str | None = None
    unidade: str | None = None
    preco: float | None = None
    tipo_catalogo: str | None = None
    ref_global: int | None = None
    ativo: bool | None = None

    @field_validator("tipo_catalogo")
    @classmethod
    def tipo_catalogo_valido(cls, v: str | None) -> str | None:
        if v is not None and v not in ("material", "equipamento"):
            raise ValueError("tipo_catalogo deve ser 'material' ou 'equipamento'.")
        return v


class ProdutoEmpresaOut(BaseModel):
    id: int
    descricao: str
    codigo_interno: str | None
    unidade: str
    preco: float
    tipo_catalogo: str | None
    ref_global: int | None
    ativo: bool

    model_config = {"from_attributes": True}


class ItemMapaPreco(BaseModel):
    preco: float
    fonte: str  # 'lista_empresa' | 'cotacao_historico'
    descricao: str
