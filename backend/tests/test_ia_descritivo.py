"""Redação por IA do descritivo técnico — trava por empresa no BACKEND (cada geração
custa uma chamada de IA), validação de números e teto por hora. A chamada real à
Anthropic é sempre substituída por um dublê: a suíte nunca gasta crédito de IA."""
from uuid import uuid4

import pytest

from app.api import routes_ia
from app.main import app
from app.schemas.auth import UserOut
from app.services.auth import get_current_user
from app.services.ia_descritivo import numeros_fora_dos_fatos

FATOS = {"secoes": [{"titulo": "Resultado", "paragrafos": [
    "A carga térmica líquida é de 4.369 kcal/h.",
    "A capacidade requerida é de 6.409 kcal/h, com o compressor operando 18 h/dia.",
    "Margem de segurança de 10,0%.",
]}]}


def _usuario(habilitado: bool, empresa_id=None) -> UserOut:
    return UserOut(
        id=uuid4(), username="u", email="u@x.com", is_active=True,
        empresa_id=empresa_id or uuid4(), empresa_ia_descritivo_habilitado=habilitado,
    )


@pytest.fixture
def como_usuario():
    def _ativar(u):
        app.dependency_overrides[get_current_user] = lambda: u
    yield _ativar
    app.dependency_overrides.pop(get_current_user, None)
    routes_ia._chamadas.clear()


@pytest.fixture
def ia_falsa(monkeypatch):
    chamadas = []

    async def _fake(secoes):
        chamadas.append(secoes)
        return "Texto gerado de teste.", []

    monkeypatch.setattr(routes_ia, "gerar_descritivo_ia", _fake)
    return chamadas


@pytest.mark.asyncio
async def test_ia_1_empresa_sem_flag_leva_403_e_nao_chama_a_ia(client, como_usuario, ia_falsa):
    como_usuario(_usuario(habilitado=False))
    r = await client.post("/api/v1/ia/descritivo", json=FATOS)
    assert r.status_code == 403
    assert ia_falsa == []  # nem tentou — gasto zero


@pytest.mark.asyncio
async def test_ia_2_empresa_com_flag_gera_texto(client, como_usuario, ia_falsa):
    como_usuario(_usuario(habilitado=True))
    r = await client.post("/api/v1/ia/descritivo", json=FATOS)
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["texto"] == "Texto gerado de teste."
    assert corpo["numeros_fora_dos_fatos"] == []
    assert len(ia_falsa) == 1


@pytest.mark.asyncio
async def test_ia_3_sem_autenticacao_leva_401_ou_403(client):
    r = await client.post("/api/v1/ia/descritivo", json=FATOS)
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_ia_4_payload_invalido_leva_422(client, como_usuario, ia_falsa):
    como_usuario(_usuario(habilitado=True))
    assert (await client.post("/api/v1/ia/descritivo", json={"secoes": []})).status_code == 422
    grande = {"secoes": [{"titulo": "x", "paragrafos": ["a" * 1501]}]}
    assert (await client.post("/api/v1/ia/descritivo", json=grande)).status_code == 422
    assert ia_falsa == []


@pytest.mark.asyncio
async def test_ia_5_teto_por_hora_devolve_429(client, como_usuario, ia_falsa, monkeypatch):
    monkeypatch.setattr(routes_ia, "_MAX_POR_HORA", 2)
    como_usuario(_usuario(habilitado=True))
    assert (await client.post("/api/v1/ia/descritivo", json=FATOS)).status_code == 200
    assert (await client.post("/api/v1/ia/descritivo", json=FATOS)).status_code == 200
    assert (await client.post("/api/v1/ia/descritivo", json=FATOS)).status_code == 429
    assert len(ia_falsa) == 2


@pytest.mark.asyncio
async def test_ia_6_falha_da_ia_vira_erro_amigavel_sem_vazar_detalhe(client, como_usuario, monkeypatch):
    async def _quebra(secoes):
        raise Exception("segredo interno sk-ant-xxx")

    monkeypatch.setattr(routes_ia, "gerar_descritivo_ia", _quebra)
    como_usuario(_usuario(habilitado=True))
    r = await client.post("/api/v1/ia/descritivo", json=FATOS)
    assert r.status_code == 502
    assert "sk-ant" not in r.text


def test_ia_7_numeros_fora_dos_fatos():
    fatos = "- A carga é de 4.369 kcal/h. - Margem de 10,0%. - Compressor operando 18 h/dia."
    assert numeros_fora_dos_fatos("Carga de 4.369 kcal/h, margem de 10% e 18 h/dia.", fatos) == []
    # separador de milhar diferente e ".0" omitido não contam como número novo
    assert numeros_fora_dos_fatos("Carga de 4,369 kcal/h e margem de 10,0%.", fatos) == []
    # número inventado é apontado; inteiro de 1 dígito (contagem) é ignorado
    assert numeros_fora_dos_fatos("Garantia de 24 meses para 2 unidades, 5.000 kcal/h.", fatos) == ["24", "5.000"]
