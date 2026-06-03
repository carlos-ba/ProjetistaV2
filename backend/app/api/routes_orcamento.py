from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database.session import get_db
from app.schemas.orcamento import OrcamentoRequest, OrcamentoResponse
from app.services.orcamento import gerar_orcamento
from app.services.cotacao import gerar_planilha_cotacao

router = APIRouter(prefix="/api/v1/orcamento", tags=["orcamento"])


@router.post("", response_model=OrcamentoResponse)
async def gerar_orcamento_endpoint(
    payload: OrcamentoRequest,
    db: AsyncSession = Depends(get_db),
) -> OrcamentoResponse:
    return await gerar_orcamento(payload, db)


# ── Schema da cotação ──────────────────────────────────────────────────────
class ItemCotacao(BaseModel):
    id: Optional[int] = None
    tipo: str                   # Equipamento | Material | Componente
    item: str
    detalhe: str = ""
    quantidade: float = 1
    unidade: str = "un"


class CotacaoRequest(BaseModel):
    itens: list[ItemCotacao]
    nome_projeto: str = "Projeto"
    nome_cliente: str = ""


@router.post("/cotacao")
async def gerar_cotacao_endpoint(payload: CotacaoRequest):
    """
    Gera planilha Excel de cotação para envio ao fornecedor.
    O fornecedor preenche a coluna de Preço Unitário e devolve.
    """
    itens = [i.model_dump() for i in payload.itens]
    xlsx_bytes = gerar_planilha_cotacao(
        itens=itens,
        nome_projeto=payload.nome_projeto,
        nome_cliente=payload.nome_cliente,
    )
    filename = f"Cotacao_{payload.nome_projeto.replace(' ', '_')}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
