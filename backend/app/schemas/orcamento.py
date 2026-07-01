from pydantic import BaseModel


class ItemOrcamento(BaseModel):
    id: int | None = None
    qtde: float
    item: str | None = None
    detalhe: str = ""
    preco_unitario: float | None = None
    categoria: str | None = None


class OrcamentoRequest(BaseModel):
    materiais: list[ItemOrcamento] = []
    equipamentos: list[ItemOrcamento] = []


class ItemDetalhado(BaseModel):
    item: str
    quantidade: float
    unidade: str
    custo_unitario_rs: float
    custo_total_rs: float
    detalhe: str
    categoria: str | None = None


class OrcamentoResponse(BaseModel):
    custo_total_materiais_rs: float
    custo_total_equipamentos_rs: float
    custo_total_projeto_rs: float
    detalhamento_itens: list[ItemDetalhado]
