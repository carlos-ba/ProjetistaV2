from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth import (
    UserCreate, UserLogin, TokenResponse, TokenRefreshRequest, TokenRefreshResponse,
    MessageResponse, ForgotPasswordRequest, ResetPasswordRequest, UserOut, PreferenciasUpdate,
    EncerrarSessaoLoginRequest,
)
from app.services.auth import (
    registrar_usuario, autenticar_usuario, renovar_token,
    verificar_email, solicitar_reset_senha, redefinir_senha, get_current_user, encerrar_sessao,
    encerrar_sessao_e_entrar,
)

_bearer = HTTPBearer()


def _ip_do_cliente(request: Request) -> str | None:
    # Atrás do proxy do Render, request.client.host é o IP do proxy — o IP real do
    # cliente vem no X-Forwarded-For (primeiro da lista, os demais são proxies intermediários).
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None

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
async def login(payload: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    return await autenticar_usuario(
        payload.username, payload.password, db,
        ip=_ip_do_cliente(request), user_agent=request.headers.get("user-agent"),
    )


@router.post("/token/encerrar-sessao/", response_model=TokenResponse)
async def login_encerrando_sessao(
    payload: EncerrarSessaoLoginRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    """Segunda etapa do login quando o limite de sessões foi atingido: o usuário
    escolheu, na lista devolvida pelo 403 de /token/, qual sessão encerrar."""
    return await encerrar_sessao_e_entrar(
        payload.username, payload.password, payload.sessao_id, db,
        ip=_ip_do_cliente(request), user_agent=request.headers.get("user-agent"),
    )


@router.post("/logout/", response_model=MessageResponse)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Logout real — revoga a sessão no servidor (o botão "Sair" antes só limpava
    o navegador; o token continuava criptograficamente válido até expirar sozinho)."""
    await encerrar_sessao(credentials.credentials, db)
    return MessageResponse(detail="Sessão encerrada.")


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
