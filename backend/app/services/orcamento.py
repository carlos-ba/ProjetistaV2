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
        if i.id:
            result = await db.execute(select(Material).where(Material.id == i.id))
            mat = result.scalar_one_or_none()
            if mat:
                custo = float(mat.custo)
                subtotal = i.qtde * custo
                total_mat += subtotal
                itens.append(ItemDetalhado(
                    item=f"(Mat) {mat.nome}",
                    quantidade=i.qtde,
                    unidade=mat.unidade_medida_id and "un",
                    custo_unitario_rs=custo,
                    custo_total_rs=round(subtotal, 2),
                    detalhe=i.detalhe,
                ))
        else:
            itens.append(ItemDetalhado(
                item=i.item or "Item Dimensionado",
                quantidade=i.qtde,
                unidade="un",
                custo_unitario_rs=0.0,
                custo_total_rs=0.0,
                detalhe=i.detalhe,
            ))

    for i in req.equipamentos:
        if i.id:
            result = await db.execute(
                select(Equipamento).where(Equipamento.id == i.id)
            )
            eq = result.scalar_one_or_none()
            if eq:
                custo = float(eq.custo)
                subtotal = i.qtde * custo
                total_eq += subtotal
                itens.append(ItemDetalhado(
                    item=f"(Eq) {eq.modelo}",
                    quantidade=i.qtde,
                    unidade="un",
                    custo_unitario_rs=custo,
                    custo_total_rs=round(subtotal, 2),
                    detalhe=i.detalhe,
                ))
        else:
            itens.append(ItemDetalhado(
                item=i.item or "Equipamento Dimensionado",
                quantidade=i.qtde,
                unidade="un",
                custo_unitario_rs=0.0,
                custo_total_rs=0.0,
                detalhe=i.detalhe,
            ))

    return OrcamentoResponse(
        custo_total_materiais_rs=round(total_mat, 2),
        custo_total_equipamentos_rs=round(total_eq, 2),
        custo_total_projeto_rs=round(total_mat + total_eq, 2),
        detalhamento_itens=itens,
    )
