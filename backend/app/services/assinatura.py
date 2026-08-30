"""Trava de escrita para trial vencido + limite de projetos durante o trial.

DESIGN_TRIAL_15_DIAS — decisão de 2026-08-25 (docs/decisoes/). `plano`
(técnico/empresa) é só o produto contratado; "trial" é exclusivamente um
`status_assinatura` — fase temporária de qualquer produto antes da
assinatura ser confirmada (ver docs/decisoes/2026-08-30-plano-x-status.md).
Ponto de extensão futuro: quando o checkout de terceiro for plugado, a
ativação de assinatura (webhook -> troca de status/prazo) entra aqui
também, como função que o admin manual e o webhook chamam por igual.
"""
from __future__ import annotations
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.empresa import Empresa, LIMITE_PROJETOS_TRIAL
from app.models.projeto import Projeto
from app.services.auth import get_empresa_atual


async def _obter_empresa(db: AsyncSession, empresa_id: UUID) -> Empresa:
    empresa = await db.get(Empresa, empresa_id)
    if empresa is None:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return empresa


async def exigir_pode_editar(
    empresa_id: UUID = Depends(get_empresa_atual),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """Dependency para rotas de escrita: bloqueia quando o trial venceu.

    Leitura e exportação continuam liberadas — essas rotas seguem usando
    get_empresa_atual diretamente, não esta dependency.
    """
    empresa = await _obter_empresa(db, empresa_id)
    if empresa.trial_expirado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Período de avaliação encerrado. Assine um plano para continuar "
                   "editando — seus projetos continuam disponíveis para visualização "
                   "e exportação.",
        )
    return empresa_id


async def exigir_limite_projetos_trial(db: AsyncSession, empresa_id: UUID) -> None:
    """Durante o trial (status_assinatura=='trial'), só LIMITE_PROJETOS_TRIAL
    projeto(s) por empresa — vale pra qualquer plano, não só técnico."""
    empresa = await _obter_empresa(db, empresa_id)
    if empresa.status_assinatura != "trial":
        return
    total = await db.scalar(
        select(func.count(Projeto.id)).where(Projeto.empresa_id == empresa_id)
    )
    if (total or 0) >= LIMITE_PROJETOS_TRIAL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"O plano de avaliação permite apenas {LIMITE_PROJETOS_TRIAL} "
                   "projeto. Assine um plano para criar mais.",
        )
