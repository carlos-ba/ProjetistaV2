"""Administração IceNexus — gestão de empresas (tenants) e seus usuários.

Restrito ao papel `superadmin_icenexus`. É por aqui que a implantação de um cliente
empresa é feita: cria-se a empresa e os usuários da equipe dela.

O cadastro público (/api/auth/register/) continua criando 1 empresa por usuário —
serve ao profissional individual. Usuários ADICIONAIS de uma empresa existente só
nascem aqui.
"""
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.database.session import get_db
from app.models.empresa import Empresa, PAPEL_ADMIN, PAPEL_MEMBRO
from app.models.usuario import Usuario
from app.models.sessao_usuario import SessaoUsuario
from app.schemas.auth import UserOut
from app.schemas.produto_empresa import ProdutoEmpresaCreate, ProdutoEmpresaUpdate, ProdutoEmpresaOut
from app.services.auth import exigir_superadmin
from app.services.produto_empresa import listar_produtos, criar_produto, atualizar_produto, remover_produto

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
    recursos_avancados_habilitados: bool | None = None


class EmpresaOut(BaseModel):
    id: UUID
    nome: str
    cnpj: str | None
    plano: str
    status_assinatura: str
    assinatura_inicio: date | None
    assinatura_fim: date | None
    recursos_avancados_habilitados: bool = False
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


class UsuarioUpdate(BaseModel):
    is_active: bool | None = None
    papel: str | None = None
    email: EmailStr | None = None
    # Redefinição pelo admin: não há autoatendimento por e-mail garantido, então
    # este é o caminho confiável para destravar quem esqueceu a senha.
    password: str | None = None

    @field_validator("papel")
    @classmethod
    def papel_valido(cls, v: str | None) -> str | None:
        if v is not None and v not in PAPEIS_PERMITIDOS:
            raise ValueError(f"Papel deve ser um de: {', '.join(PAPEIS_PERMITIDOS)}")
        return v

    @field_validator("password")
    @classmethod
    def senha_minima(cls, v: str | None) -> str | None:
        if v is not None and len(v) < 8:
            raise ValueError("Senha deve ter ao menos 8 caracteres.")
        return v


class UsuarioAdminOut(BaseModel):
    id: UUID
    username: str
    email: str
    papel: str
    is_active: bool
    email_verified: bool
    # Métrica de visibilidade (DESIGN_LIMITE_SESSOES_2026-08-16.md) — só subsídio pro
    # admin investigar, NÃO bloqueia nada automaticamente. IP é sinal ruidoso pra
    # técnico de campo em 4G/5G.
    sessoes_ativas: int = 0
    ips_distintos_hoje: int = 0

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
    usuarios = result.scalars().all()
    if not usuarios:
        return []

    # Sessões ativas + IPs distintos nas últimas 24h, por usuário — só visibilidade
    # pro admin (ver DESIGN_LIMITE_SESSOES_2026-08-16.md), não bloqueia nada.
    desde = datetime.now(timezone.utc) - timedelta(days=1)
    metricas = await db.execute(
        select(
            SessaoUsuario.usuario_id,
            func.count().filter(SessaoUsuario.revogada_em.is_(None)),
            func.count(func.distinct(SessaoUsuario.ip)).filter(SessaoUsuario.created_at >= desde),
        )
        .where(SessaoUsuario.usuario_id.in_([u.id for u in usuarios]))
        .group_by(SessaoUsuario.usuario_id)
    )
    por_usuario = {uid: (ativas, ips) for uid, ativas, ips in metricas.all()}

    return [
        UsuarioAdminOut.model_validate(u).model_copy(update={
            "sessoes_ativas": por_usuario.get(u.id, (0, 0))[0],
            "ips_distintos_hoje": por_usuario.get(u.id, (0, 0))[1],
        })
        for u in usuarios
    ]


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


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioAdminOut)
async def atualizar_usuario(
    usuario_id: UUID,
    payload: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    admin: UserOut = Depends(exigir_superadmin),
):
    """Ativa/desativa o acesso e ajusta o papel.

    Desativar precisa ser reversível: username e e-mail são únicos, então um
    usuário desativado não pode ser recriado — sem reativação, o acesso ficaria
    permanentemente perdido.
    """
    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    dados = payload.model_dump(exclude_unset=True)
    if usuario_id == admin.id and dados.get("is_active") is False:
        raise HTTPException(status_code=400, detail="Não é possível desativar a própria conta.")

    # E-mail é único: barra o conflito com mensagem clara em vez de erro de banco
    novo_email = dados.pop("email", None)
    if novo_email and novo_email != usuario.email:
        existe = (await db.execute(
            select(Usuario).where(Usuario.email == novo_email, Usuario.id != usuario_id)
        )).scalar_one_or_none()
        if existe:
            raise HTTPException(status_code=400, detail={"email": ["Este e-mail já está cadastrado."]})
        usuario.email = novo_email

    # Senha nova é gravada como hash; qualquer token de reset pendente é invalidado
    nova_senha = dados.pop("password", None)
    if nova_senha:
        usuario.hashed_password = hash_password(nova_senha)
        usuario.password_reset_token = None

    for campo, valor in dados.items():
        setattr(usuario, campo, valor)
    await db.commit()
    await db.refresh(usuario)
    return usuario


# ── Lista de preços de uma empresa (implantação — Fase B) ──────────────────

@router.get("/empresas/{empresa_id}/produtos", response_model=list[ProdutoEmpresaOut])
async def listar_produtos_empresa(
    empresa_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UserOut = Depends(exigir_superadmin),
):
    await _obter_empresa(db, empresa_id)
    return await listar_produtos(db, empresa_id)


@router.post("/empresas/{empresa_id}/produtos", response_model=ProdutoEmpresaOut,
             status_code=status.HTTP_201_CREATED)
async def criar_produto_empresa(
    empresa_id: UUID,
    payload: ProdutoEmpresaCreate,
    db: AsyncSession = Depends(get_db),
    _: UserOut = Depends(exigir_superadmin),
):
    await _obter_empresa(db, empresa_id)
    return await criar_produto(db, empresa_id, payload)


@router.patch("/empresas/{empresa_id}/produtos/{produto_id}", response_model=ProdutoEmpresaOut)
async def atualizar_produto_empresa(
    empresa_id: UUID,
    produto_id: int,
    payload: ProdutoEmpresaUpdate,
    db: AsyncSession = Depends(get_db),
    _: UserOut = Depends(exigir_superadmin),
):
    await _obter_empresa(db, empresa_id)
    return await atualizar_produto(db, empresa_id, produto_id, payload)


@router.delete("/empresas/{empresa_id}/produtos/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_produto_empresa(
    empresa_id: UUID,
    produto_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserOut = Depends(exigir_superadmin),
):
    await _obter_empresa(db, empresa_id)
    await remover_produto(db, empresa_id, produto_id)


async def _obter_empresa(db: AsyncSession, empresa_id: UUID) -> Empresa:
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return empresa
