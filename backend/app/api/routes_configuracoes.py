from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database.session import get_db
from app.models.configuracao_montagem import ConfiguracaoMontagem
from app.schemas.auth import UserOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/configuracoes", tags=["configuracoes"])

DEFAULTS = dict(
    tipo_filtro="solda", tipo_visor="solda",
    trecho_vet_evap=0.5, trecho_evap_sifao=0.5,
    trecho_subida=1.0, trecho_sifao_gbc=0.5,
)


class PerfilPayload(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    tipo_filtro: str = Field("solda")
    tipo_visor: str = Field("solda")
    trecho_vet_evap: float = Field(0.5, gt=0)
    trecho_evap_sifao: float = Field(0.5, gt=0)
    trecho_subida: float = Field(1.0, gt=0)
    trecho_sifao_gbc: float = Field(0.5, gt=0)


def _to_dict(cfg: ConfiguracaoMontagem) -> dict:
    return {
        "id": cfg.id,
        "nome": cfg.nome,
        "ativo": cfg.ativo,
        "tipo_filtro": cfg.tipo_filtro,
        "tipo_visor": cfg.tipo_visor,
        "trecho_vet_evap": float(cfg.trecho_vet_evap),
        "trecho_evap_sifao": float(cfg.trecho_evap_sifao),
        "trecho_subida": float(cfg.trecho_subida),
        "trecho_sifao_gbc": float(cfg.trecho_sifao_gbc),
    }


async def _garantir_padrao(db: AsyncSession, usuario_id: UUID):
    """Cria perfil padrão se o usuário ainda não tem nenhum."""
    result = await db.execute(
        select(ConfiguracaoMontagem).where(ConfiguracaoMontagem.usuario_id == usuario_id)
    )
    if result.scalars().first() is None:
        padrao = ConfiguracaoMontagem(usuario_id=usuario_id, nome="Padrão", ativo=True, **DEFAULTS)
        db.add(padrao)
        await db.commit()


@router.get("/montagem")
async def listar_perfis(
    usuario: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _garantir_padrao(db, usuario.id)
    result = await db.execute(
        select(ConfiguracaoMontagem)
        .where(ConfiguracaoMontagem.usuario_id == usuario.id)
        .order_by(ConfiguracaoMontagem.id)
    )
    return [_to_dict(c) for c in result.scalars().all()]


@router.post("/montagem", status_code=201)
async def criar_perfil(
    payload: PerfilPayload,
    usuario: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cfg = ConfiguracaoMontagem(usuario_id=usuario.id, **payload.model_dump())
    db.add(cfg)
    await db.commit()
    await db.refresh(cfg)
    return _to_dict(cfg)


@router.put("/montagem/{perfil_id}")
async def atualizar_perfil(
    perfil_id: int,
    payload: PerfilPayload,
    usuario: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConfiguracaoMontagem)
        .where(ConfiguracaoMontagem.id == perfil_id, ConfiguracaoMontagem.usuario_id == usuario.id)
    )
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(404, "Perfil não encontrado")
    for k, v in payload.model_dump().items():
        setattr(cfg, k, v)
    await db.commit()
    await db.refresh(cfg)
    return _to_dict(cfg)


@router.patch("/montagem/{perfil_id}/ativar")
async def ativar_perfil(
    perfil_id: int,
    usuario: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ativa um perfil e desativa todos os outros do usuário."""
    result = await db.execute(
        select(ConfiguracaoMontagem)
        .where(ConfiguracaoMontagem.usuario_id == usuario.id)
    )
    perfis = result.scalars().all()
    alvo = next((p for p in perfis if p.id == perfil_id), None)
    if not alvo:
        raise HTTPException(404, "Perfil não encontrado")
    for p in perfis:
        p.ativo = (p.id == perfil_id)
    await db.commit()
    return _to_dict(alvo)


@router.delete("/montagem/{perfil_id}", status_code=204)
async def deletar_perfil(
    perfil_id: int,
    usuario: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConfiguracaoMontagem)
        .where(ConfiguracaoMontagem.id == perfil_id, ConfiguracaoMontagem.usuario_id == usuario.id)
    )
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(404, "Perfil não encontrado")
    await db.delete(cfg)
    await db.commit()
