"""Fixtures compartilhadas dos testes — primeira infraestrutura de teste
automatizado do projeto (não havia pytest configurado antes desta feature).

Estratégia de isolamento: cada teste cria sua própria Empresa (e Usuario,
quando precisa) via factory, contra o banco local de desenvolvimento (mesma
DATABASE_URL do `.env`, nunca produção). A fixture de empresa apaga tudo que
criou (na ordem certa, por causa do FK RESTRICT de usuario->empresa) ao
final do teste — não depende de rollback de transação aninhada, mais simples
de entender e auditar numa primeira suíte de testes.

NUNCA rodar contra DATABASE_URL de produção.
"""
import asyncio
import sys
from datetime import date, timedelta
from uuid import uuid4

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.security import hash_password
from app.database.session import SessionLocal, get_db
from app.main import app
from app.models.assinatura_gateway import AssinaturaGateway
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.webhook_checkout_evento import WebhookCheckoutEvento


@pytest_asyncio.fixture
async def db():
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def empresa_factory(db):
    criadas: list = []

    async def _criar(**overrides):
        defaults = dict(
            nome=f"Empresa Teste {uuid4().hex[:8]}",
            plano="tecnico",
            status_assinatura="trial",
            assinatura_inicio=date.today(),
            assinatura_fim=date.today() + timedelta(days=15),
        )
        defaults.update(overrides)
        empresa = Empresa(**defaults)
        db.add(empresa)
        await db.commit()
        await db.refresh(empresa)
        criadas.append(empresa.id)
        return empresa

    yield _criar

    for empresa_id in criadas:
        await db.execute(delete(WebhookCheckoutEvento).where(WebhookCheckoutEvento.empresa_id == empresa_id))
        await db.execute(delete(AssinaturaGateway).where(AssinaturaGateway.empresa_id == empresa_id))
        await db.execute(delete(Usuario).where(Usuario.empresa_id == empresa_id))
        await db.execute(delete(Empresa).where(Empresa.id == empresa_id))
    await db.commit()


@pytest_asyncio.fixture
async def usuario_factory(db):
    async def _criar(empresa, email: str | None = None, username: str | None = None):
        usuario = Usuario(
            username=username or f"user_{uuid4().hex[:8]}",
            email=email or f"{uuid4().hex[:8]}@teste.local",
            hashed_password=hash_password("senha123456"),
            empresa_id=empresa.id,
            email_verified=True,
        )
        db.add(usuario)
        await db.commit()
        await db.refresh(usuario)
        return usuario

    return _criar


@pytest_asyncio.fixture
async def client():
    async def _override_get_db():
        async with SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_get_db
    # raise_app_exceptions=False: uma exceção não tratada deve virar um 500
    # de verdade na resposta (igual um servidor real via uvicorn), não
    # propagar pro teste — é exatamente o que o teste 21 verifica.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def token_themembers(monkeypatch):
    """Configura token + IDs de produto de teste em `settings` pra duração
    do teste (revertido sozinho pelo monkeypatch)."""
    from app.core.config import settings

    token = "token-teste-" + uuid4().hex
    monkeypatch.setattr(settings, "THEMEMBERS_WEBHOOK_TOKEN", token)
    monkeypatch.setattr(settings, "THEMEMBERS_PRODUCT_MONTHLY_ID", "prod-mensal-001")
    monkeypatch.setattr(settings, "THEMEMBERS_PRODUCT_SEMIANNUAL_ID", "prod-semestral-002")
    monkeypatch.setattr(settings, "THEMEMBERS_PRODUCT_PREMIUM_ID", "prod-premium-003")
    return token
