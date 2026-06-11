from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.cotacao import Fornecedor, Cotacao, CotacaoItem
from app.schemas.auth import UserOut
from app.schemas.cotacao import (
    FornecedorCreate, FornecedorUpdate, FornecedorOut,
    CotacaoCreate, CotacaoOut, CotacaoComItens,
)
from app.services.auth import get_current_user
from app.services.cotacao_excel import gerar_planilha_cotacao_v2

router = APIRouter(prefix="/api/v1/cotacoes", tags=["cotacoes"])


# ── Fornecedores ────────────────────────────────────────────────────────────

@router.post("/fornecedores", response_model=FornecedorOut, status_code=status.HTTP_201_CREATED)
async def criar_fornecedor(
    payload: FornecedorCreate,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    fornecedor = Fornecedor(owner_id=usuario.id, **payload.model_dump())
    db.add(fornecedor)
    await db.commit()
    await db.refresh(fornecedor)
    return fornecedor


@router.get("/fornecedores", response_model=list[FornecedorOut])
async def listar_fornecedores(
    incluir_inativos: bool = False,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    stmt = select(Fornecedor).where(Fornecedor.owner_id == usuario.id)
    if not incluir_inativos:
        stmt = stmt.where(Fornecedor.ativo.is_(True))
    result = await db.execute(stmt.order_by(Fornecedor.nome))
    return result.scalars().all()


@router.patch("/fornecedores/{fornecedor_id}", response_model=FornecedorOut)
async def atualizar_fornecedor(
    fornecedor_id: int,
    payload: FornecedorUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    fornecedor = await _obter_fornecedor(db, fornecedor_id, usuario.id)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(fornecedor, campo, valor)
    await db.commit()
    await db.refresh(fornecedor)
    return fornecedor


@router.delete("/fornecedores/{fornecedor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def desativar_fornecedor(
    fornecedor_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    """Desativa (soft delete) — preserva o histórico de cotações."""
    fornecedor = await _obter_fornecedor(db, fornecedor_id, usuario.id)
    fornecedor.ativo = False
    await db.commit()
    return None


async def _obter_fornecedor(db: AsyncSession, fornecedor_id: int, owner_id) -> Fornecedor:
    result = await db.execute(
        select(Fornecedor).where(
            Fornecedor.id == fornecedor_id,
            Fornecedor.owner_id == owner_id,
        )
    )
    fornecedor = result.scalar_one_or_none()
    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    return fornecedor


# ── Cotações ────────────────────────────────────────────────────────────────

async def _gerar_codigo(db: AsyncSession, fornecedor_id: int) -> str:
    ano = datetime.now().year
    result = await db.execute(
        select(func.count(Cotacao.id)).where(
            func.extract("year", Cotacao.created_at) == ano
        )
    )
    seq = (result.scalar() or 0) + 1
    return f"COT-{ano}-{seq:04d}-F{fornecedor_id:03d}"


@router.post("", response_model=CotacaoOut, status_code=status.HTTP_201_CREATED)
async def criar_cotacao(
    payload: CotacaoCreate,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    if not payload.itens:
        raise HTTPException(status_code=422, detail="A cotação precisa ter ao menos um item")

    await _obter_fornecedor(db, payload.fornecedor_id, usuario.id)
    codigo = await _gerar_codigo(db, payload.fornecedor_id)

    cotacao = Cotacao(
        codigo=codigo,
        owner_id=usuario.id,
        fornecedor_id=payload.fornecedor_id,
        projeto_id=payload.projeto_id,
        nome_projeto=payload.nome_projeto,
        validade_dias=payload.validade_dias,
        observacoes=payload.observacoes,
        status="rascunho",
    )
    db.add(cotacao)
    await db.flush()

    for item in payload.itens:
        db.add(CotacaoItem(cotacao_id=cotacao.id, **item.model_dump()))

    await db.commit()
    await db.refresh(cotacao)
    return cotacao


@router.get("", response_model=list[CotacaoOut])
async def listar_cotacoes(
    fornecedor_id: int | None = None,
    projeto_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    stmt = select(Cotacao).where(Cotacao.owner_id == usuario.id)
    if fornecedor_id:
        stmt = stmt.where(Cotacao.fornecedor_id == fornecedor_id)
    if projeto_id:
        stmt = stmt.where(Cotacao.projeto_id == projeto_id)
    result = await db.execute(stmt.order_by(Cotacao.created_at.desc()))
    return result.scalars().all()


@router.get("/{cotacao_id}", response_model=CotacaoComItens)
async def obter_cotacao(
    cotacao_id: UUID,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    return await _obter_cotacao_com_itens(db, cotacao_id, usuario.id)


@router.get("/{cotacao_id}/excel")
async def baixar_excel_cotacao(
    cotacao_id: UUID,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    cotacao = await _obter_cotacao_com_itens(db, cotacao_id, usuario.id)

    result = await db.execute(
        select(Fornecedor).where(Fornecedor.id == cotacao.fornecedor_id)
    )
    fornecedor = result.scalar_one()

    itens = [
        {
            "ref_id": i.ref_id,
            "tipo": i.tipo_item,
            "descricao": i.descricao,
            "detalhe": i.detalhe or "",
            "qtde": float(i.qtde),
            "unidade": i.unidade,
        }
        for i in cotacao.itens
    ]

    xlsx = gerar_planilha_cotacao_v2(
        codigo=cotacao.codigo,
        itens=itens,
        fornecedor_nome=fornecedor.nome,
        fornecedor_contato=fornecedor.contato or fornecedor.telefone or "",
        nome_projeto=cotacao.nome_projeto or "Projeto",
        validade_dias=cotacao.validade_dias,
    )

    # Marca como enviada no primeiro download
    if cotacao.status == "rascunho":
        cotacao.status = "enviada"
        await db.commit()

    filename = f"{cotacao.codigo}.xlsx"
    return Response(
        content=xlsx,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{cotacao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancelar_cotacao(
    cotacao_id: UUID,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    """Cancela a cotação (soft) — preserva o registro para o histórico."""
    cotacao = await _obter_cotacao_com_itens(db, cotacao_id, usuario.id)
    cotacao.status = "cancelada"
    await db.commit()
    return None


async def _obter_cotacao_com_itens(db: AsyncSession, cotacao_id: UUID, owner_id) -> Cotacao:
    result = await db.execute(
        select(Cotacao)
        .where(Cotacao.id == cotacao_id, Cotacao.owner_id == owner_id)
        .options(selectinload(Cotacao.itens))
    )
    cotacao = result.scalar_one_or_none()
    if not cotacao:
        raise HTTPException(status_code=404, detail="Cotação não encontrada")
    return cotacao
