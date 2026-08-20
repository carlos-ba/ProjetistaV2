from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.matching import norm
from app.models.produto_empresa import ProdutoEmpresa
from app.models.cotacao import Cotacao, CotacaoItem
from app.schemas.produto_empresa import ProdutoEmpresaCreate, ProdutoEmpresaUpdate


async def listar_produtos(db: AsyncSession, empresa_id: UUID) -> list[ProdutoEmpresa]:
    result = await db.execute(
        select(ProdutoEmpresa)
        .where(ProdutoEmpresa.empresa_id == empresa_id)
        .order_by(ProdutoEmpresa.descricao)
    )
    return list(result.scalars().all())


async def criar_produto(db: AsyncSession, empresa_id: UUID, payload: ProdutoEmpresaCreate) -> ProdutoEmpresa:
    produto = ProdutoEmpresa(empresa_id=empresa_id, **payload.model_dump())
    db.add(produto)
    await db.commit()
    await db.refresh(produto)
    return produto


async def _obter_produto(db: AsyncSession, empresa_id: UUID, produto_id: int) -> ProdutoEmpresa:
    result = await db.execute(
        select(ProdutoEmpresa).where(
            ProdutoEmpresa.id == produto_id, ProdutoEmpresa.empresa_id == empresa_id
        )
    )
    produto = result.scalar_one_or_none()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto


async def atualizar_produto(
    db: AsyncSession, empresa_id: UUID, produto_id: int, payload: ProdutoEmpresaUpdate
) -> ProdutoEmpresa:
    produto = await _obter_produto(db, empresa_id, produto_id)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(produto, campo, valor)
    await db.commit()
    await db.refresh(produto)
    return produto


async def remover_produto(db: AsyncSession, empresa_id: UUID, produto_id: int) -> None:
    produto = await _obter_produto(db, empresa_id, produto_id)
    await db.delete(produto)
    await db.commit()


async def obter_mapa_precos(db: AsyncSession, empresa_id: UUID) -> dict[str, dict]:
    """Cascata de preço "automática" da empresa (sem contar o preço de cotação já
    escolhido pelo usuário pra este projeto, que é injetado à parte pelo frontend):

    1. Lista de preços da própria empresa (`produto_empresa`, ativo)
    2. Última cotação confirmada da empresa pra aquele item, qualquer projeto

    Casamento por descrição normalizada — ver `app/core/matching.py` (nem todo item do
    orçamento carrega um id estável de catálogo: painéis, portas e materiais extras do
    gabinete não têm `ref_id`, só descrição).
    """
    mapa: dict[str, dict] = {}

    # Camada 2 — cotação histórica (mais recente primeiro; a primeira ocorrência de
    # cada descrição normalizada vence, então processa antes da lista da empresa pra
    # ser sobrescrita por ela).
    historico = await db.execute(
        select(CotacaoItem.descricao, CotacaoItem.preco_unitario, Cotacao.created_at)
        .join(Cotacao, Cotacao.id == CotacaoItem.cotacao_id)
        .where(Cotacao.empresa_id == empresa_id, CotacaoItem.preco_unitario.isnot(None))
        .order_by(Cotacao.created_at.desc())
    )
    for descricao, preco, _criado_em in historico.all():
        chave = norm(descricao)
        if chave not in mapa:
            mapa[chave] = {"preco": float(preco), "fonte": "cotacao_historico", "descricao": descricao}

    # Camada 1 — lista de preços da empresa (tem prioridade, sobrescreve a cotação histórica)
    produtos = await listar_produtos(db, empresa_id)
    for produto in produtos:
        if not produto.ativo:
            continue
        chave = norm(produto.descricao)
        mapa[chave] = {"preco": float(produto.preco), "fonte": "lista_empresa", "descricao": produto.descricao}

    return mapa
