from __future__ import annotations

import secrets
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.user_agent import descrever_dispositivo
from app.database.session import get_db
from app.models.usuario import Usuario
from app.models.empresa import Empresa, PAPEL_ADMIN, PAPEL_SUPERADMIN, PAPEL_MEMBRO, DURACAO_TRIAL_DIAS
from app.models.sessao_usuario import SessaoUsuario
from app.schemas.auth import UserCreate, TokenResponse, TokenRefreshResponse, UserOut
from app.services.email import enviar_verificacao_email, enviar_reset_senha

_bearer = HTTPBearer()

# DESIGN_LIMITE_SESSOES_2026-08-16.md — decisão fechada em 2026-08-19: 2 sessões
# simultâneas por usuário, fixo no código (Fase B/planos ainda não existe pra
# tornar isso configurável por empresa).
LIMITE_SESSOES = 2


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
    # Cadastro público é só a jornada técnico (self-serve) — empresa (revenda/
    # montadora) nasce via implantação assistida no admin, nunca por aqui.
    hoje = date.today()
    empresa = Empresa(
        nome=payload.username,
        plano="tecnico",
        status_assinatura="trial",
        assinatura_inicio=hoje,
        assinatura_fim=hoje + timedelta(days=DURACAO_TRIAL_DIAS),
    )
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


async def _validar_credenciais(username: str, password: str, db: AsyncSession) -> Usuario:
    result = await db.execute(select(Usuario).where(Usuario.username == username))
    usuario = result.scalar_one_or_none()

    if not usuario or not verify_password(password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos.",
        )
    if not usuario.is_active:
        raise HTTPException(status_code=400, detail="Conta desativada.")
    return usuario


async def _emitir_tokens(
    usuario: Usuario, db: AsyncSession, ip: str | None, user_agent: str | None,
) -> TokenResponse:
    sessao = SessaoUsuario(usuario_id=usuario.id, ip=ip, user_agent=user_agent)
    db.add(sessao)
    await db.flush()

    user_id = str(usuario.id)
    session_id = str(sessao.id)
    access = create_access_token(usuario.username, user_id, session_id)
    refresh = create_refresh_token(user_id, session_id)
    await db.commit()
    return TokenResponse(access=access, refresh=refresh, email_verified=usuario.email_verified)


async def autenticar_usuario(
    username: str, password: str, db: AsyncSession,
    ip: str | None = None, user_agent: str | None = None,
) -> TokenResponse:
    usuario = await _validar_credenciais(username, password, db)

    result = await db.execute(
        select(SessaoUsuario)
        .where(SessaoUsuario.usuario_id == usuario.id, SessaoUsuario.revogada_em.is_(None))
        .order_by(SessaoUsuario.ultimo_uso_em.asc())
    )
    sessoes = result.scalars().all()
    if len(sessoes) >= LIMITE_SESSOES:
        # Bloqueia (não derruba a sessão antiga em silêncio — decisão de
        # DESIGN_LIMITE_SESSOES_2026-08-16.md), mas devolve a lista de sessões
        # ativas pra o usuário poder encerrar uma delas explicitamente e continuar
        # — sem isso, uma sessão esquecida aberta (aba fechada sem logout) trava o
        # login em qualquer outro dispositivo até o token expirar sozinho em até 30
        # dias (REFRESH_TOKEN_EXPIRE_DAYS) ou alguém rodar a limpeza manual.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "erro": "limite_sessoes",
                "mensagem": f"Limite de {LIMITE_SESSOES} sessões simultâneas atingido. "
                            "Encerre uma sessão abaixo para continuar.",
                "sessoes": [
                    {
                        "id": str(s.id),
                        "dispositivo": descrever_dispositivo(s.user_agent),
                        "ip": s.ip,
                        "ultimo_uso_em": s.ultimo_uso_em.isoformat() if s.ultimo_uso_em else None,
                    }
                    for s in sessoes
                ],
            },
        )

    return await _emitir_tokens(usuario, db, ip, user_agent)


async def encerrar_sessao_e_entrar(
    username: str, password: str, sessao_id: UUID, db: AsyncSession,
    ip: str | None = None, user_agent: str | None = None,
) -> TokenResponse:
    """Segunda etapa do fluxo de limite de sessões: usuário já provou a senha uma vez
    (recebeu a lista no 403 de autenticar_usuario) e escolheu qual sessão encerrar.
    Reexige a senha aqui — mais simples e seguro que emitir um token intermediário só
    pra essa decisão, e o usuário acabou de digitá-la mesmo."""
    usuario = await _validar_credenciais(username, password, db)

    result = await db.execute(
        select(SessaoUsuario).where(
            SessaoUsuario.id == sessao_id, SessaoUsuario.usuario_id == usuario.id,
        )
    )
    sessao = result.scalar_one_or_none()
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    if sessao.revogada_em is None:
        sessao.revogada_em = datetime.now(timezone.utc)
        await db.commit()

    return await _emitir_tokens(usuario, db, ip, user_agent)


async def encerrar_sessao(access_token: str, db: AsyncSession) -> None:
    """Logout real — revoga a sessão no servidor. Falha em silêncio se o token já
    estiver expirado/inválido: nesse caso a sessão já é inútil, não há o que revogar."""
    try:
        payload = decode_token(access_token)
        sid = payload.get("sid")
    except JWTError:
        return
    if not sid:
        return

    result = await db.execute(select(SessaoUsuario).where(SessaoUsuario.id == UUID(sid)))
    sessao = result.scalar_one_or_none()
    if sessao and sessao.revogada_em is None:
        sessao.revogada_em = datetime.now(timezone.utc)
        await db.commit()


async def renovar_token(refresh_token: str, db: AsyncSession) -> TokenRefreshResponse:
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError
        user_id = payload.get("sub")
        sid = payload.get("sid")
        if not user_id or not sid:
            raise ValueError
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Token de refresh inválido.")

    result = await db.execute(select(Usuario).where(Usuario.id == UUID(user_id)))
    usuario = result.scalar_one_or_none()
    if not usuario or not usuario.is_active:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")

    sessao = (await db.execute(
        select(SessaoUsuario).where(SessaoUsuario.id == UUID(sid))
    )).scalar_one_or_none()
    if not sessao or sessao.revogada_em is not None:
        raise HTTPException(status_code=401, detail="Sessão encerrada. Faça login novamente.")

    sessao.ultimo_uso_em = datetime.now(timezone.utc)
    await db.commit()

    return TokenRefreshResponse(
        access=create_access_token(usuario.username, str(usuario.id), sid)
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
        sid = payload.get("sid")
        if not user_id or not sid:
            raise ValueError
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )

    sessao = (await db.execute(
        select(SessaoUsuario).where(SessaoUsuario.id == UUID(sid))
    )).scalar_one_or_none()
    if not sessao or sessao.revogada_em is not None:
        raise HTTPException(status_code=401, detail="Sessão encerrada. Faça login novamente.")

    result = await db.execute(
        select(Usuario).options(selectinload(Usuario.empresa)).where(Usuario.id == UUID(user_id))
    )
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
