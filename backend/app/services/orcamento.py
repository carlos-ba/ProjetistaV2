from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.equipamento import Equipamento
from app.models.material import Material
from app.schemas.orcamento import OrcamentoRequest, OrcamentoResponse, ItemDetalhado


async def gerar_orcamento(req: OrcamentoRequest, db: AsyncSession) -> OrcamentoResponse:
    itens: list[ItemDetalhado] = []
    total_mat = 0.0
    total_eq = 0.0

    for i in req.materiais:
        # Preço injetado pelo frontend tem prioridade — cotação do projeto, senão a
        # cascata da empresa (lista própria → última cotação histórica), resolvida no
        # frontend antes de chamar este endpoint (ver GeradorOrcamento.jsx). O catálogo
        # global (Material.custo) não é mais fonte de preço (Fase B) — só de nome, quando
        # o frontend não mandou um.
        nome = i.item
        if not nome and i.id:
            result = await db.execute(select(Material).where(Material.id == i.id))
            mat = result.scalar_one_or_none()
            nome = f"(Mat) {mat.nome}" if mat else None
        nome = nome or "Item Dimensionado"
        custo = i.preco_unitario if i.preco_unitario is not None else 0.0
        unidade = "un"
        subtotal = i.qtde * custo
        total_mat += subtotal
        itens.append(ItemDetalhado(
            item=nome,
            quantidade=i.qtde,
            unidade=unidade,
            custo_unitario_rs=custo,
            custo_total_rs=round(subtotal, 2),
            detalhe=i.detalhe,
            categoria=i.categoria,
            tipo_item=i.tipo_item,
        ))

    for i in req.equipamentos:
        nome = i.item
        if not nome and i.id:
            result = await db.execute(select(Equipamento).where(Equipamento.id == i.id))
            eq = result.scalar_one_or_none()
            nome = f"(Eq) {eq.modelo}" if eq else None
        nome = nome or "Equipamento Dimensionado"
        custo = i.preco_unitario if i.preco_unitario is not None else 0.0
        subtotal = i.qtde * custo
        total_eq += subtotal
        itens.append(ItemDetalhado(
            item=nome,
            quantidade=i.qtde,
            unidade="un",
            custo_unitario_rs=custo,
            custo_total_rs=round(subtotal, 2),
            detalhe=i.detalhe,
            categoria=i.categoria or "equipamento",
            tipo_item=i.tipo_item,
        ))

    return OrcamentoResponse(
        custo_total_materiais_rs=round(total_mat, 2),
        custo_total_equipamentos_rs=round(total_eq, 2),
        custo_total_projeto_rs=round(total_mat + total_eq, 2),
        detalhamento_itens=itens,
    )
