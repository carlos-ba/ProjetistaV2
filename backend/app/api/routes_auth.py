from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.auth import UserCreate, UserLogin, TokenResponse, TokenRefreshRequest, TokenRefreshResponse, MessageResponse
from app.services.auth import registrar_usuario, autenticar_usuario, renovar_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await registrar_usuario(payload, db)
    return MessageResponse(detail="Usuário criado.")


@router.post("/token/", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    return await autenticar_usuario(payload.username, payload.password, db)


@router.post("/token/refresh/", response_model=TokenRefreshResponse)
async def refresh_token(payload: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    return await renovar_token(payload.refresh, db)
