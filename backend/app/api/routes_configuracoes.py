import re
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database.session import get_db
from app.models.configuracao_montagem import ConfiguracaoMontagem
from app.models.empresa import Empresa
from app.schemas.auth import UserOut
from app.services.auth import get_current_user, get_empresa_atual

router = APIRouter(prefix="/api/v1/configuracoes", tags=["configuracoes"])

# Base64 de imagem pequena (~200KB) já cobre um logo redimensionado no
# navegador antes de enviar — teto aqui é só rede de segurança, a compressão
# de verdade acontece no frontend (canvas resize).
LOGO_BASE64_MAX_CHARS = 300_000

DEFAULTS = dict(
    tipo_filtro="solda", tipo_visor="solda",
    trecho_vet_evap=0.5, trecho_evap_sifao=0.5,
    trecho_subida=1.0, trecho_sifao_gbc=0.5,
    incluir_filtro=False, incluir_visor=False,
    incluir_gbc_entrada=False, incluir_gbc_saida=False,
    largura_aba_padrao_mm=40, rendimento_selante_m_por_embalagem=12.0,
)


class PerfilPayload(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    tipo_filtro: str = Field("solda")
    tipo_visor: str = Field("solda")
    trecho_vet_evap: float = Field(0.5, gt=0)
    trecho_evap_sifao: float = Field(0.5, gt=0)
    trecho_subida: float = Field(1.0, gt=0)
    trecho_sifao_gbc: float = Field(0.5, gt=0)
    incluir_filtro:      bool = Field(True)
    incluir_visor:       bool = Field(True)
    incluir_gbc_entrada: bool = Field(True)
    incluir_gbc_saida:   bool = Field(True)
    largura_aba_padrao_mm: int = Field(40, gt=0)
    rendimento_selante_m_por_embalagem: float = Field(12.0, gt=0)


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
        "incluir_filtro":      cfg.incluir_filtro,
        "incluir_visor":       cfg.incluir_visor,
        "incluir_gbc_entrada": cfg.incluir_gbc_entrada,
        "incluir_gbc_saida":   cfg.incluir_gbc_saida,
        "largura_aba_padrao_mm": cfg.largura_aba_padrao_mm,
        "rendimento_selante_m_por_embalagem": float(cfg.rendimento_selante_m_por_embalagem),
    }


async def _garantir_padrao(db: AsyncSession, empresa_id: UUID, usuario_id: UUID):
    """Cria perfil padrão se a empresa ainda não tem nenhum.

    O perfil é da EMPRESA (compartilhado pela equipe); usuario_id fica como autor.
    """
    result = await db.execute(
        select(ConfiguracaoMontagem).where(ConfiguracaoMontagem.empresa_id == empresa_id)
    )
    if result.scalars().first() is None:
        padrao = ConfiguracaoMontagem(
            empresa_id=empresa_id, usuario_id=usuario_id, nome="Padrão", ativo=True, **DEFAULTS
        )
        db.add(padrao)
        await db.commit()


@router.get("/montagem")
async def listar_perfis(
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
    db: AsyncSession = Depends(get_db),
):
    await _garantir_padrao(db, empresa_id, usuario.id)
    result = await db.execute(
        select(ConfiguracaoMontagem)
        .where(ConfiguracaoMontagem.empresa_id == empresa_id)
        .order_by(ConfiguracaoMontagem.id)
    )
    return [_to_dict(c) for c in result.scalars().all()]


@router.post("/montagem", status_code=201)
async def criar_perfil(
    payload: PerfilPayload,
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
    db: AsyncSession = Depends(get_db),
):
    cfg = ConfiguracaoMontagem(usuario_id=usuario.id, empresa_id=empresa_id, **payload.model_dump())
    db.add(cfg)
    await db.commit()
    await db.refresh(cfg)
    return _to_dict(cfg)


@router.put("/montagem/{perfil_id}")
async def atualizar_perfil(
    perfil_id: int,
    payload: PerfilPayload,
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConfiguracaoMontagem)
        .where(ConfiguracaoMontagem.id == perfil_id, ConfiguracaoMontagem.empresa_id == empresa_id)
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
    empresa_id: UUID = Depends(get_empresa_atual),
    db: AsyncSession = Depends(get_db),
):
    """Ativa um perfil e desativa todos os outros do usuário."""
    result = await db.execute(
        select(ConfiguracaoMontagem)
        .where(ConfiguracaoMontagem.empresa_id == empresa_id)
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
    empresa_id: UUID = Depends(get_empresa_atual),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConfiguracaoMontagem)
        .where(ConfiguracaoMontagem.id == perfil_id, ConfiguracaoMontagem.empresa_id == empresa_id)
    )
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(404, "Perfil não encontrado")
    await db.delete(cfg)
    await db.commit()


# ── Identidade da Proposta ──────────────────────────────────────────────
# Marca do técnico (nome da firma, logo, contato) que aparece na proposta ao
# cliente (Card 6) — qualquer membro da empresa edita, sem gate de admin:
# não é área sensível de conta, é o próprio técnico personalizando o que
# entrega pro próprio cliente.

class IdentidadePropostaOut(BaseModel):
    proposta_nome: str | None = None
    proposta_logo_base64: str | None = None
    proposta_contato_nome: str | None = None
    proposta_contato_telefone: str | None = None

    model_config = {"from_attributes": True}


class IdentidadePropostaUpdate(BaseModel):
    proposta_nome: str | None = Field(None, max_length=200)
    proposta_logo_base64: str | None = Field(None, max_length=LOGO_BASE64_MAX_CHARS)
    proposta_contato_nome: str | None = Field(None, max_length=150)
    proposta_contato_telefone: str | None = None

    @field_validator("proposta_contato_telefone")
    @classmethod
    def telefone_valido(cls, v: str | None) -> str | None:
        # Opcional (diferente do telefone obrigatório do cadastro) — só valida
        # formato quando algo foi informado.
        if not v or not v.strip():
            return None
        digitos = re.sub(r"\D", "", v)
        if len(digitos) not in (10, 11):
            raise ValueError("Celular de contato inválido — informe DDD + número.")
        return digitos


async def _buscar_empresa(db: AsyncSession, empresa_id: UUID) -> Empresa:
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(404, "Empresa não encontrada")
    return empresa


@router.get("/identidade-proposta", response_model=IdentidadePropostaOut)
async def obter_identidade_proposta(
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
    db: AsyncSession = Depends(get_db),
):
    empresa = await _buscar_empresa(db, empresa_id)
    return empresa


@router.patch("/identidade-proposta", response_model=IdentidadePropostaOut)
async def atualizar_identidade_proposta(
    payload: IdentidadePropostaUpdate,
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
    db: AsyncSession = Depends(get_db),
):
    empresa = await _buscar_empresa(db, empresa_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(empresa, k, v)
    await db.commit()
    await db.refresh(empresa)
    return empresa
