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
        # Preco injetado pelo frontend (da cotação) tem prioridade; fallback para banco
        if i.preco_unitario is not None:
            custo = i.preco_unitario
            nome = i.item or "Item Dimensionado"
            unidade = "un"
        elif i.id:
            result = await db.execute(select(Material).where(Material.id == i.id))
            mat = result.scalar_one_or_none()
            custo = float(mat.custo) if mat else 0.0
            nome = f"(Mat) {mat.nome}" if mat else (i.item or "Item Dimensionado")
            unidade = "un"
        else:
            custo = 0.0
            nome = i.item or "Item Dimensionado"
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
        if i.preco_unitario is not None:
            custo = i.preco_unitario
            nome = i.item or "Equipamento Dimensionado"
        elif i.id:
            result = await db.execute(select(Equipamento).where(Equipamento.id == i.id))
            eq = result.scalar_one_or_none()
            custo = float(eq.custo) if eq else 0.0
            nome = f"(Eq) {eq.modelo}" if eq else (i.item or "Equipamento Dimensionado")
        else:
            custo = 0.0
            nome = i.item or "Equipamento Dimensionado"
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
