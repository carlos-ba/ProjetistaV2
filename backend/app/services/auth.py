from __future__ import annotations

import secrets
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.database.session import get_db
from app.models.usuario import Usuario
from app.models.empresa import Empresa, PAPEL_ADMIN, PAPEL_SUPERADMIN, PAPEL_MEMBRO
from app.schemas.auth import UserCreate, TokenResponse, TokenRefreshResponse, UserOut
from app.services.email import enviar_verificacao_email, enviar_reset_senha

_bearer = HTTPBearer()


async def registrar_usuario(payload: UserCreate, db: AsyncSession) -> Usuario:
    existing = await db.execute(select(Usuario).where(Usuario.username == payload.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail={"username": ["Este usuário já existe."]})

    existing_email = await db.execute(select(Usuario).where(Usuario.email == payload.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail={"email": ["Este e-mail já está cadastrado."]})

    token_verificacao = secrets.token_urlsafe(32)

    # Todo usuário nasce dono da própria empresa (tenant). Usuários adicionais de
    # uma empresa existente são criados pelo endpoint de admin, não por aqui.
    empresa = Empresa(nome=payload.username, plano="trial", status_assinatura="ativa")
    db.add(empresa)
    await db.flush()

    usuario = Usuario(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        email_verified=False,
        email_verification_token=token_verificacao,
        empresa_id=empresa.id,
        papel=PAPEL_ADMIN,
    )
    db.add(usuario)
    await db.flush()
    await db.refresh(usuario)
    await db.commit()

    # Envia email de verificação (falha silenciosa se email não configurado)
    try:
        await enviar_verificacao_email(usuario.email, token_verificacao)
    except Exception:
        pass

    return usuario


async def verificar_email(token: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(Usuario).where(Usuario.email_verification_token == token)
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=400, detail="Token de verificação inválido ou expirado.")

    usuario.email_verified = True
    usuario.email_verification_token = None
    await db.commit()


async def solicitar_reset_senha(email: str, db: AsyncSession) -> None:
    result = await db.execute(select(Usuario).where(Usuario.email == email))
    usuario = result.scalar_one_or_none()

    # Resposta genérica: não revelar se o email existe ou não
    if not usuario:
        return

    token_reset = secrets.token_urlsafe(32)
    usuario.password_reset_token = token_reset
    await db.commit()

    try:
        await enviar_reset_senha(usuario.email, token_reset)
    except Exception:
        pass


async def redefinir_senha(token: str, nova_senha: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(Usuario).where(Usuario.password_reset_token == token)
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=400, detail="Token de redefinição inválido ou expirado.")

    usuario.hashed_password = hash_password(nova_senha)
    usuario.password_reset_token = None
    await db.commit()


async def autenticar_usuario(username: str, password: str, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(Usuario).where(Usuario.username == username))
    usuario = result.scalar_one_or_none()

    if not usuario or not verify_password(password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos.",
        )
    if not usuario.is_active:
        raise HTTPException(status_code=400, detail="Conta desativada.")

    user_id = str(usuario.id)
    return TokenResponse(
        access=create_access_token(usuario.username, user_id),
        refresh=create_refresh_token(user_id),
        email_verified=usuario.email_verified,
    )


async def renovar_token(refresh_token: str, db: AsyncSession) -> TokenRefreshResponse:
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Token de refresh inválido.")

    result = await db.execute(select(Usuario).where(Usuario.id == UUID(user_id)))
    usuario = result.scalar_one_or_none()
    if not usuario or not usuario.is_active:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")

    return TokenRefreshResponse(
        access=create_access_token(usuario.username, str(usuario.id))
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise ValueError
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )

    result = await db.execute(select(Usuario).where(Usuario.id == UUID(user_id)))
    usuario = result.scalar_one_or_none()
    if not usuario or not usuario.is_active:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")
    return UserOut.model_validate(usuario)


async def get_empresa_atual(usuario: UserOut = Depends(get_current_user)) -> UUID:
    """Escopo multi-tenant: devolve a empresa do usuário logado.

    Falha explicitamente se o usuário não tiver empresa vinculada — sem isso, uma
    query escopada filtraria por NULL e retornaria vazio silenciosamente (ou pior,
    vazaria dados se alguém esquecesse o filtro).
    """
    if not usuario.empresa_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário sem empresa vinculada. Contate o administrador.",
        )
    return usuario.empresa_id


async def exigir_superadmin(usuario: UserOut = Depends(get_current_user)) -> UserOut:
    """Restringe a rota à equipe IceNexus (papel superadmin_icenexus)."""
    if usuario.papel != PAPEL_SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito à administração IceNexus.",
        )
    return usuario
