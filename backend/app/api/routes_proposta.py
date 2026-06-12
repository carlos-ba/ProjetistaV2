"""
Fase 3 — Comparativo de cotações e Proposta Comercial.

Comparativo: agrupa itens por descrição entre as cotações processadas,
mostrando o preço de cada fornecedor e o melhor preço por item.

Proposta: persiste a composição completa (fonte de preços, custos do usuário,
margem, impostos, condições comerciais) em JSON.
"""
import re
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.cotacao import Cotacao
from app.models.proposta import PropostaComercial
from app.schemas.auth import UserOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/propostas", tags=["propostas"])


# ── Comparativo de cotações ─────────────────────────────────────────────────

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip().lower())


@router.get("/comparativo")
async def comparativo_cotacoes(
    projeto_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    """
    Compara as cotações processadas do usuário, item a item.
    Retorna por item: preço de cada fornecedor + melhor preço.
    """
    stmt = (
        select(Cotacao)
        .where(Cotacao.owner_id == usuario.id, Cotacao.status == "processada")
        .options(selectinload(Cotacao.itens), selectinload(Cotacao.fornecedor))
        .order_by(Cotacao.created_at.desc())
    )
    if projeto_id:
        stmt = stmt.where(Cotacao.projeto_id == projeto_id)

    result = await db.execute(stmt)
    cotacoes = result.scalars().unique().all()

    if not cotacoes:
        return {"cotacoes": [], "itens": [], "totais": {}}

    # Cabeçalho das cotações comparadas
    cabecalho = [
        {
            "cotacao_id": str(c.id),
            "codigo": c.codigo,
            "fornecedor": c.fornecedor.nome,
            "data_recebimento": c.data_recebimento,
            "nome_projeto": c.nome_projeto,
            "projeto_id": str(c.projeto_id) if c.projeto_id else None,
        }
        for c in cotacoes
    ]

    # Agrupar itens por descrição normalizada
    itens_map: dict[str, dict[str, Any]] = {}
    for c in cotacoes:
        for item in c.itens:
            chave = _norm(item.descricao)
            if chave not in itens_map:
                itens_map[chave] = {
                    "descricao": item.descricao,
                    "qtde": float(item.qtde),
                    "unidade": item.unidade,
                    "tipo_item": item.tipo_item,
                    "precos": {},   # codigo da cotação → dados
                }
            preco = float(item.preco_unitario) if item.preco_unitario else None
            itens_map[chave]["precos"][c.codigo] = {
                "preco_unitario": preco,
                "marca_modelo": item.marca_modelo_cotado,
                "prazo_dias": item.prazo_entrega_dias,
                "fornecedor": c.fornecedor.nome,
            }

    # Melhor preço por item
    itens = []
    for dados in itens_map.values():
        validos = {k: v for k, v in dados["precos"].items() if v["preco_unitario"]}
        melhor = min(validos.items(), key=lambda kv: kv[1]["preco_unitario"]) if validos else None
        dados["melhor"] = {
            "codigo": melhor[0],
            "fornecedor": melhor[1]["fornecedor"],
            "preco_unitario": melhor[1]["preco_unitario"],
        } if melhor else None
        itens.append(dados)

    # Totais por cotação + total "melhores preços"
    totais: dict[str, float] = {c.codigo: 0.0 for c in cotacoes}
    total_melhores = 0.0
    completas: dict[str, bool] = {c.codigo: True for c in cotacoes}
    for it in itens:
        for codigo in totais:
            p = it["precos"].get(codigo, {}).get("preco_unitario")
            if p:
                totais[codigo] += p * it["qtde"]
            else:
                completas[codigo] = False
        if it["melhor"]:
            total_melhores += it["melhor"]["preco_unitario"] * it["qtde"]

    return {
        "cotacoes": cabecalho,
        "itens": itens,
        "totais": {
            "por_cotacao": [
                {"codigo": k, "total": round(v, 2), "completa": completas[k]}
                for k, v in totais.items()
            ],
            "melhores_precos": round(total_melhores, 2),
        },
    }


# ── Proposta Comercial ──────────────────────────────────────────────────────

class PropostaCreate(BaseModel):
    projeto_id: UUID | None = None
    dados: dict[str, Any]


class PropostaUpdate(BaseModel):
    status: str | None = None
    dados: dict[str, Any] | None = None


class PropostaOut(BaseModel):
    id: UUID
    codigo: str
    projeto_id: UUID | None
    status: str
    dados: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


async def _gerar_codigo_proposta(db: AsyncSession) -> str:
    """Próximo código a partir do MAIOR existente — imune a exclusões."""
    ano = datetime.now().year
    result = await db.execute(
        select(func.max(PropostaComercial.codigo)).where(
            PropostaComercial.codigo.like(f"PROP-{ano}-%")
        )
    )
    ultimo = result.scalar()
    seq = (int(ultimo.split("-")[2]) + 1) if ultimo else 1
    return f"PROP-{ano}-{seq:04d}"


@router.post("", response_model=PropostaOut, status_code=status.HTTP_201_CREATED)
async def criar_proposta(
    payload: PropostaCreate,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    proposta = PropostaComercial(
        codigo=await _gerar_codigo_proposta(db),
        owner_id=usuario.id,
        projeto_id=payload.projeto_id,
        dados=payload.dados,
        status="rascunho",
    )
    db.add(proposta)
    await db.commit()
    await db.refresh(proposta)
    return proposta


@router.get("", response_model=list[PropostaOut])
async def listar_propostas(
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    result = await db.execute(
        select(PropostaComercial)
        .where(PropostaComercial.owner_id == usuario.id)
        .order_by(PropostaComercial.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{proposta_id}", response_model=PropostaOut)
async def obter_proposta(
    proposta_id: UUID,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    return await _obter(db, proposta_id, usuario.id)


@router.patch("/{proposta_id}", response_model=PropostaOut)
async def atualizar_proposta(
    proposta_id: UUID,
    payload: PropostaUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    proposta = await _obter(db, proposta_id, usuario.id)
    if payload.status is not None:
        if payload.status not in ("rascunho", "enviada", "aceita", "recusada"):
            raise HTTPException(status_code=422, detail="Status inválido")
        proposta.status = payload.status
    if payload.dados is not None:
        proposta.dados = payload.dados
    await db.commit()
    await db.refresh(proposta)
    return proposta


@router.delete("/{proposta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_proposta(
    proposta_id: UUID,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
):
    proposta = await _obter(db, proposta_id, usuario.id)
    await db.delete(proposta)
    await db.commit()
    return None


async def _obter(db: AsyncSession, proposta_id: UUID, owner_id) -> PropostaComercial:
    result = await db.execute(
        select(PropostaComercial).where(
            PropostaComercial.id == proposta_id,
            PropostaComercial.owner_id == owner_id,
        )
    )
    proposta = result.scalar_one_or_none()
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    return proposta
