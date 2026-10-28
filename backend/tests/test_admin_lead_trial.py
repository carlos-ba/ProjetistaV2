"""Sinalizador de trial novo no painel Administração (specs/001-sinalizador-trial-novo).

Controle comercial do superadmin: empresa em trial nasce "não tratada" (bolinha vermelha) e só o
clique manual do superadmin a marca como tratada (verde). O campo `lead_tratado_em` vazio = pendente.
Não altera assinatura nem nada que o cliente enxergue.
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.main import app
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.schemas.auth import UserOut
from app.services import auth as servico_auth
from app.services.auth import get_current_user


def _usuario(papel: str) -> UserOut:
    return UserOut(
        id=uuid4(), username="u", email="u@x.com", is_active=True,
        empresa_id=uuid4(), papel=papel,
    )


@pytest.fixture
def como_usuario():
    def _ativar(u):
        app.dependency_overrides[get_current_user] = lambda: u
    yield _ativar
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def sem_email(monkeypatch):
    """O cadastro público tenta enviar e-mail de verificação — nunca de verdade nos testes."""
    async def _nao_envia(*a, **k):
        return None
    monkeypatch.setattr(servico_auth, "enviar_verificacao_email", _nao_envia)


async def _item(client, empresa_id):
    r = await client.get("/api/v1/admin/empresas")
    assert r.status_code == 200
    return next(e for e in r.json() if e["id"] == str(empresa_id))


@pytest.mark.asyncio
async def test_lead_1_cadastro_publico_nasce_pendente(client, db, como_usuario, sem_email):
    sufixo = uuid4().hex[:8]
    r = await client.post("/api/auth/register/", json={
        "username": f"lead_{sufixo}", "email": f"lead_{sufixo}@teste-lead.com.br",   # EmailStr recusa o TLD ".local"
        "password": "senha123456", "telefone": "71999998888",
    })
    assert r.status_code == 201
    try:
        usuario = (await db.execute(select(Usuario).where(Usuario.username == f"lead_{sufixo}"))).scalar_one()
        como_usuario(_usuario("superadmin_icenexus"))
        item = await _item(client, usuario.empresa_id)
        assert item["status_assinatura"] == "trial"
        assert item["lead_tratado_em"] is None   # vermelho
    finally:
        await db.rollback()
        emp_id = (await db.execute(select(Usuario.empresa_id).where(Usuario.username == f"lead_{sufixo}"))).scalar()
        await db.execute(delete(Usuario).where(Usuario.username == f"lead_{sufixo}"))
        if emp_id:
            await db.execute(delete(Empresa).where(Empresa.id == emp_id))
        await db.commit()


@pytest.mark.asyncio
async def test_lead_2_marcar_e_desfazer(client, empresa_factory, como_usuario):
    empresa = await empresa_factory()
    como_usuario(_usuario("superadmin_icenexus"))

    r = await client.patch(f"/api/v1/admin/empresas/{empresa.id}", json={"lead_tratado": True})
    assert r.status_code == 200
    marcado = r.json()["lead_tratado_em"]
    assert marcado is not None                      # verde
    assert datetime.fromisoformat(marcado).tzinfo is not None   # UTC explícito (sem o bug do "-1 dias")
    assert (await _item(client, empresa.id))["lead_tratado_em"] == marcado

    r = await client.patch(f"/api/v1/admin/empresas/{empresa.id}", json={"lead_tratado": False})
    assert r.status_code == 200
    assert r.json()["lead_tratado_em"] is None      # volta a vermelho


@pytest.mark.asyncio
async def test_lead_3_empresa_criada_pelo_superadmin_nao_nasce_pendente(client, empresa_factory, db, como_usuario):
    como_usuario(_usuario("superadmin_icenexus"))
    nome = f"Implantacao {uuid4().hex[:8]}"
    r = await client.post("/api/v1/admin/empresas", json={"nome": nome, "status_assinatura": "trial"})
    assert r.status_code == 201
    try:
        assert r.json()["lead_tratado_em"] is not None
    finally:
        await db.execute(delete(Empresa).where(Empresa.id == r.json()["id"]))
        await db.commit()


@pytest.mark.asyncio
@pytest.mark.parametrize("papel", ["admin_empresa", "membro"])
async def test_lead_4_so_superadmin_marca(client, empresa_factory, como_usuario, papel):
    empresa = await empresa_factory()
    como_usuario(_usuario(papel))
    r = await client.patch(f"/api/v1/admin/empresas/{empresa.id}", json={"lead_tratado": True})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_lead_5_marcar_nao_altera_a_assinatura(client, empresa_factory, db, como_usuario):
    empresa = await empresa_factory()
    antes = (empresa.plano, empresa.status_assinatura, empresa.assinatura_inicio, empresa.assinatura_fim,
             empresa.nome, empresa.recursos_avancados_habilitados, empresa.ia_descritivo_habilitado)
    como_usuario(_usuario("superadmin_icenexus"))
    r = await client.patch(f"/api/v1/admin/empresas/{empresa.id}", json={"lead_tratado": True})
    assert r.status_code == 200
    await db.refresh(empresa)
    depois = (empresa.plano, empresa.status_assinatura, empresa.assinatura_inicio, empresa.assinatura_fim,
              empresa.nome, empresa.recursos_avancados_habilitados, empresa.ia_descritivo_habilitado)
    assert depois == antes


@pytest.mark.asyncio
async def test_lead_6_patch_de_outros_campos_nao_mexe_no_sinalizador(client, empresa_factory, db, como_usuario):
    empresa = await empresa_factory()
    como_usuario(_usuario("superadmin_icenexus"))
    r = await client.patch(f"/api/v1/admin/empresas/{empresa.id}", json={"nome": "Outro nome"})
    assert r.status_code == 200
    assert r.json()["lead_tratado_em"] is None     # editar a empresa não "trata" o lead
