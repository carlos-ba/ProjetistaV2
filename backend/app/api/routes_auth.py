from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth import (
    UserCreate, UserLogin, TokenResponse, TokenRefreshRequest, TokenRefreshResponse,
    MessageResponse, ForgotPasswordRequest, ResetPasswordRequest, UserOut, PreferenciasUpdate,
)
from app.services.auth import (
    registrar_usuario, autenticar_usuario, renovar_token,
    verificar_email, solicitar_reset_senha, redefinir_senha, get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me/", response_model=UserOut)
async def me(usuario: UserOut = Depends(get_current_user)) -> UserOut:
    return usuario


@router.patch("/me/preferencias/", response_model=UserOut)
async def atualizar_preferencias(
    payload: PreferenciasUpdate,
    usuario: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    obj = (await db.execute(
        select(Usuario).options(selectinload(Usuario.empresa)).where(Usuario.id == usuario.id)
    )).scalar_one()
    obj.modo_engenharia = payload.modo_engenharia
    await db.commit()
    await db.refresh(obj)
    return UserOut.model_validate(obj)


@router.post("/register/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await registrar_usuario(payload, db)
    return MessageResponse(detail="Usuário criado. Verifique seu email para ativar a conta.")


@router.post("/token/", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    return await autenticar_usuario(payload.username, payload.password, db)


@router.post("/token/refresh/", response_model=TokenRefreshResponse)
async def refresh_token(payload: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    return await renovar_token(payload.refresh, db)


@router.get("/verify-email/", response_model=MessageResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await verificar_email(token, db)
    return MessageResponse(detail="Email verificado com sucesso. Você já pode fazer login.")


@router.post("/forgot-password/", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    await solicitar_reset_senha(payload.email, db)
    return MessageResponse(detail="Se o email estiver cadastrado, você receberá as instruções.")


@router.post("/reset-password/", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    await redefinir_senha(payload.token, payload.nova_senha, db)
    return MessageResponse(detail="Senha redefinida com sucesso.")
