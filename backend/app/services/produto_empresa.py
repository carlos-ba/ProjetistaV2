from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass
class ItemImportacao:
    """Uma linha a importar — já convertida pra este formato por quem lê o arquivo de
    origem (cada implantação tem seu próprio conversor, ver importar_produtos_em_lote)."""
    descricao: str
    preco: float | None
    codigo_interno: str | None = None
    unidade: str = "un"


@dataclass
class ResultadoImportacao:
    inseridos: int = 0
    atualizados: int = 0
    erros: list[str] = field(default_factory=list)


async def importar_produtos_em_lote(
    db: AsyncSession, empresa_id: UUID, itens: list[ItemImportacao],
) -> ResultadoImportacao:
    """Motor de importação em lote — upsert por descrição normalizada (mesma chave da
    cascata de preço em obter_mapa_precos). Deliberadamente sem UI e sem formato de
    arquivo fixo: cada implantação de cliente traz preços num formato diferente (ERP
    próprio, planilha do fornecedor, CSV) — a peça que se repete não é o parser do
    arquivo, é validar e gravar; então só essa parte foi construída agora. Quando uma
    implantação acontecer de verdade, escreve-se um script pontual em backend/scripts/
    que lê o arquivo do cliente (formato dele) e chama esta função — ver
    project-jornada-assinatura-saas na memória para o raciocínio completo por trás
    dessa decisão.
    """
    resultado = ResultadoImportacao()
    vistos: set[str] = set()

    existentes = await listar_produtos(db, empresa_id)
    por_chave = {norm(p.descricao): p for p in existentes}

    for idx, item in enumerate(itens, start=1):
        descricao = (item.descricao or "").strip()
        if not descricao:
            resultado.erros.append(f"item {idx}: descrição vazia, ignorado")
            continue
        if item.preco is None or item.preco < 0:
            resultado.erros.append(f"item {idx} ({descricao}): preço inválido, ignorado")
            continue

        chave = norm(descricao)
        if chave in vistos:
            resultado.erros.append(
                f"item {idx} ({descricao}): descrição duplicada nesta importação, "
                "ignorado (mantida a primeira ocorrência)"
            )
            continue
        vistos.add(chave)

        existente = por_chave.get(chave)
        if existente:
            existente.descricao = descricao
            existente.preco = item.preco
            existente.codigo_interno = item.codigo_interno
            existente.unidade = item.unidade or "un"
            existente.ativo = True
            resultado.atualizados += 1
        else:
            novo = ProdutoEmpresa(
                empresa_id=empresa_id, descricao=descricao, preco=item.preco,
                codigo_interno=item.codigo_interno, unidade=item.unidade or "un",
            )
            db.add(novo)
            por_chave[chave] = novo
            resultado.inseridos += 1

    await db.commit()
    return resultado


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
