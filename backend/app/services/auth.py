from __future__ import annotations
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.database.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth import UserCreate, TokenResponse, TokenRefreshResponse, UserOut

_bearer = HTTPBearer()


async def registrar_usuario(payload: UserCreate, db: AsyncSession) -> Usuario:
    existing = await db.execute(
        select(Usuario).where(Usuario.username == payload.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail={"username": ["Este usuário já existe."]})

    existing_email = await db.execute(
        select(Usuario).where(Usuario.email == payload.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail={"email": ["Este e-mail já está cadastrado."]})

    usuario = Usuario(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(usuario)
    await db.flush()
    await db.refresh(usuario)
    await db.commit()
    return usuario


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
