from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ── Fornecedor ──────────────────────────────────────────────────────────────

class FornecedorCreate(BaseModel):
    nome: str
    cnpj: str | None = None
    telefone: str | None = None
    email: str | None = None
    contato: str | None = None


class FornecedorUpdate(BaseModel):
    nome: str | None = None
    cnpj: str | None = None
    telefone: str | None = None
    email: str | None = None
    contato: str | None = None
    ativo: bool | None = None


class FornecedorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cnpj: str | None
    telefone: str | None
    email: str | None
    contato: str | None
    ativo: bool
    created_at: datetime


# ── Cotação ─────────────────────────────────────────────────────────────────

class CotacaoItemCreate(BaseModel):
    tipo_item: str = "Material"
    ref_id: int | None = None
    descricao: str
    detalhe: str | None = None
    qtde: float = 1
    unidade: str = "un"


class CotacaoCreate(BaseModel):
    fornecedor_id: int
    projeto_id: UUID | None = None
    nome_projeto: str | None = None
    validade_dias: int = 30
    observacoes: str | None = None
    itens: list[CotacaoItemCreate]


class CotacaoItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_item: str
    ref_id: int | None
    descricao: str
    detalhe: str | None
    qtde: float
    unidade: str
    preco_unitario: float | None
    marca_modelo_cotado: str | None
    prazo_entrega_dias: int | None
    obs_fornecedor: str | None


class CotacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo: str
    fornecedor_id: int
    projeto_id: UUID | None
    nome_projeto: str | None
    status: str
    validade_dias: int
    data_recebimento: str | None
    observacoes: str | None
    created_at: datetime


class CotacaoComItens(CotacaoOut):
    itens: list[CotacaoItemOut]
