"""Administração IceNexus — gestão de empresas (tenants) e seus usuários.

Restrito ao papel `superadmin_icenexus`. É por aqui que a implantação de um cliente
empresa é feita: cria-se a empresa e os usuários da equipe dela.

O cadastro público (/api/auth/register/) continua criando 1 empresa por usuário —
serve ao profissional individual. Usuários ADICIONAIS de uma empresa existente só
nascem aqui.
"""
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.database.session import get_db
from app.models.empresa import Empresa, PAPEL_ADMIN, PAPEL_MEMBRO
from app.models.usuario import Usuario
from app.schemas.auth import UserOut
from app.services.auth import exigir_superadmin

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

PAPEIS_PERMITIDOS = (PAPEL_ADMIN, PAPEL_MEMBRO)


# ── Schemas ─────────────────────────────────────────────────────────────────

class EmpresaCreate(BaseModel):
    nome: str
    cnpj: str | None = None
    plano: str = "empresa"
    status_assinatura: str = "ativa"
    assinatura_inicio: date | None = None
    assinatura_fim: date | None = None


class EmpresaUpdate(BaseModel):
    nome: str | None = None
    cnpj: str | None = None
    plano: str | None = None
    status_assinatura: str | None = None
    assinatura_fim: date | None = None


class EmpresaOut(BaseModel):
    id: UUID
    nome: str
    cnpj: str | None
    plano: str
    status_assinatura: str
    assinatura_inicio: date | None
    assinatura_fim: date | None
    total_usuarios: int = 0

    model_config = {"from_attributes": True}


class UsuarioCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    papel: str = PAPEL_MEMBRO

    @field_validator("password")
    @classmethod
    def senha_minima(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter ao menos 8 caracteres.")
        return v

    @field_validator("papel")
    @classmethod
    def papel_valido(cls, v: str) -> str:
        if v not in PAPEIS_PERMITIDOS:
            raise ValueError(f"Papel deve ser um de: {', '.join(PAPEIS_PERMITIDOS)}")
        return v


class UsuarioAdminOut(BaseModel):
    id: UUID
    username: str
    email: str
    papel: str
    is_active: bool
    email_verified: bool

    model_config = {"from_attributes": True}


# ── Empresas ────────────────────────────────────────────────────────────────

@router.get("/empresas", response_model=list[EmpresaOut])
async def listar_empresas(
    db: AsyncSession = Depends(get_db),
    _: UserOut = Depends(exigir_superadmin),
):
    result = await db.execute(
        select(Empresa, func.count(Usuario.id))
        .outerjoin(Usuario, Usuario.empresa_id == Empresa.id)
        .group_by(Empresa.id)
        .order_by(Empresa.nome)
    )
    return [
        EmpresaOut(**{c.name: getattr(e, c.name) for c in Empresa.__table__.columns
                      if c.name in EmpresaOut.model_fields}, total_usuarios=n)
        for e, n in result.all()
    ]


@router.post("/empresas", response_model=EmpresaOut, status_code=status.HTTP_201_CREATED)
async def criar_empresa(
    payload: EmpresaCreate,
    db: AsyncSession = Depends(get_db),
    _: UserOut = Depends(exigir_superadmin),
):
    empresa = Empresa(**payload.model_dump())
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)
    return EmpresaOut.model_validate(empresa)


@router.patch("/empresas/{empresa_id}", response_model=EmpresaOut)
async def atualizar_empresa(
    empresa_id: UUID,
    payload: EmpresaUpdate,
    db: AsyncSession = Depends(get_db),
    _: UserOut = Depends(exigir_superadmin),
):
    empresa = await _obter_empresa(db, empresa_id)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(empresa, campo, valor)
    await db.commit()
    await db.refresh(empresa)
    return EmpresaOut.model_validate(empresa)


# ── Usuários de uma empresa ─────────────────────────────────────────────────

@router.get("/empresas/{empresa_id}/usuarios", response_model=list[UsuarioAdminOut])
async def listar_usuarios(
    empresa_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UserOut = Depends(exigir_superadmin),
):
    await _obter_empresa(db, empresa_id)
    result = await db.execute(
        select(Usuario).where(Usuario.empresa_id == empresa_id).order_by(Usuario.username)
    )
    return result.scalars().all()


@router.post("/empresas/{empresa_id}/usuarios", response_model=UsuarioAdminOut,
             status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    empresa_id: UUID,
    payload: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    _: UserOut = Depends(exigir_superadmin),
):
    """Cria um usuário dentro de uma empresa existente (fluxo de implantação).

    Já nasce com e-mail verificado: quem está cadastrando é a administração,
    não há autosserviço a confirmar.
    """
    await _obter_empresa(db, empresa_id)

    if (await db.execute(select(Usuario).where(Usuario.username == payload.username))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail={"username": ["Este usuário já existe."]})
    if (await db.execute(select(Usuario).where(Usuario.email == payload.email))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail={"email": ["Este e-mail já está cadastrado."]})

    usuario = Usuario(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        empresa_id=empresa_id,
        papel=payload.papel,
        email_verified=True,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


@router.patch("/usuarios/{usuario_id}/desativar", response_model=UsuarioAdminOut)
async def desativar_usuario(
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: UserOut = Depends(exigir_superadmin),
):
    if usuario_id == admin.id:
        raise HTTPException(status_code=400, detail="Não é possível desativar a própria conta.")
    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    usuario.is_active = False
    await db.commit()
    await db.refresh(usuario)
    return usuario


async def _obter_empresa(db: AsyncSession, empresa_id: UUID) -> Empresa:
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return empresa
