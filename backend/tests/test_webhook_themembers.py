"""22 testes obrigatórios da spec (docs/handoffs/especificacao-webhook-checkout-
themembers-2026-09-03.md §16) — numerados igual à lista da spec pra
rastreabilidade.
"""
import asyncio
import hashlib
import hmac
import json
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.models.webhook_checkout_evento import WebhookCheckoutEvento
from app.schemas.auth import UserCreate
from app.services.assinatura import exigir_pode_editar
from app.services.auth import registrar_usuario, verificar_email
from app.services.webhook_themembers import normalizar_payload, processar_webhook

URL = "/api/webhooks/themembers/checkout"


def payload_direto(event: str, data: dict, created_at: str | None = None, object_: str = "transaction"):
    body: dict = {"object": object_, "event": event, "data": data}
    if created_at:
        body["created_at"] = created_at
    return body


def payload_envelope(event: str, data: dict, id_="evt-envelope-1", object_="order"):
    return {"company": {"id": "c1"}, "payload": {"id": id_, "object": object_, "event": event, "data": data}}


async def post_assinado(client, body: dict, token: str):
    """Assina o corpo com HMAC-SHA256 (esquema real do Checkout, confirmado
    na documentação oficial em 2026-09-03 — não é mais token estático em
    x-signature). Serializa e envia via `content=` bruto, não `json=`, pra
    garantir que os bytes assinados sejam exatamente os bytes recebidos pela
    rota — qualquer diferença de serialização quebraria a assinatura."""
    corpo_bruto = json.dumps(body).encode("utf-8")
    assinatura = hmac.new(token.encode("utf-8"), corpo_bruto, hashlib.sha256).hexdigest()
    return await client.post(
        URL, content=corpo_bruto,
        headers={"x-signature": assinatura, "content-type": "application/json"},
    )


# ── 1-3: autenticação ────────────────────────────────────────────────────────

async def test_1_rejeita_token_ausente(client, token_themembers):
    r = await client.post(URL, json=payload_direto("release.access", {}))
    assert r.status_code == 401


async def test_2_rejeita_token_incorreto(client, token_themembers):
    r = await post_assinado(client, payload_direto("release.access", {}), "token-errado")
    assert r.status_code == 401


async def test_2b_rejeita_esquema_antigo_de_token_estatico(client, token_themembers):
    """Achado verificando o dashboard/documentação real da TheMembers em
    2026-09-03: o Checkout assina com HMAC-SHA256 do corpo bruto, não com
    token estático comparado direto em x-signature (era a suposição inicial
    da spec, atribuída erroneamente só à Área de Membros). Manda o token em
    texto puro no header, exatamente como o esquema antigo fazia — precisa
    ser rejeitado agora."""
    body = payload_direto("release.access", {})
    r = await client.post(URL, json=body, headers={"x-signature": token_themembers})
    assert r.status_code == 401


async def test_3_aceita_token_correto(client, token_themembers, empresa_factory, usuario_factory):
    empresa = await empresa_factory()
    await usuario_factory(empresa, email="compra3@teste.local")
    body = payload_direto("release.access", {
        "customer": {"email": "compra3@teste.local"}, "product": {"id": "prod-mensal-001"},
    })
    r = await post_assinado(client, body, token_themembers)
    assert r.status_code == 200


async def test_3b_webhook_desabilitado_por_padrao_mesmo_com_token_certo(client, monkeypatch):
    """Achado na revisão de código: THEMEMBERS_WEBHOOK_ENABLED era só validado
    no startup, nunca checado pela rota — um token configurado sem ENABLED=true
    ainda processava webhooks de verdade. Sem a fixture token_themembers
    (que liga ENABLED) — só o token, simulando exatamente esse cenário."""
    from app.core.config import settings
    token = "token-desabilitado-teste"
    monkeypatch.setattr(settings, "THEMEMBERS_WEBHOOK_TOKEN", token)
    assert settings.THEMEMBERS_WEBHOOK_ENABLED is False

    body = payload_direto("release.access", {"customer": {"email": "nao-importa@teste.local"}})
    r = await post_assinado(client, body, token)
    assert r.status_code == 503


# ── 4: normalização dos 2 formatos de envelope ───────────────────────────────

def test_4_normaliza_dois_formatos_envelope():
    direto = normalizar_payload(payload_direto("transaction.approved", {"customer": {"email": "a@b.com"}}))
    envelope = normalizar_payload(payload_envelope("transaction.approved", {"customer": {"email": "a@b.com"}}, id_="evt-x"))
    assert direto.event == "transaction.approved"
    assert envelope.event == "transaction.approved"
    assert envelope.external_id == "evt-x"
    assert direto.email_comprador == "a@b.com"
    assert envelope.email_comprador == "a@b.com"


def test_4b_data_sem_timezone_tratada_como_horario_brasilia():
    """Confirmado na documentação oficial do Checkout (verificada ao vivo em
    2026-09-03): datas vêm sem offset, formato "YYYY-MM-DD HH:MM:SS" — como a
    TheMembers/TheBank é plataforma brasileira, tratamos isso como horário de
    Brasília (UTC-3), não UTC (era o comportamento antigo, achado na mesma
    verificação)."""
    evento = normalizar_payload(payload_direto("release.access", {}, created_at="2026-01-08 18:32:19"))
    assert evento.criado_em_provedor == datetime(2026, 1, 8, 21, 32, 19, tzinfo=timezone.utc)


# ── 5-7: ativação e mapeamento de produto ────────────────────────────────────

async def test_5_release_access_ativa_empresa_existente(client, token_themembers, empresa_factory, usuario_factory, db):
    empresa = await empresa_factory(status_assinatura="trial")
    await usuario_factory(empresa, email="ativa5@teste.local")
    body = payload_direto("release.access", {
        "customer": {"email": "ativa5@teste.local"}, "product": {"id": "prod-mensal-001"},
    })
    r = await post_assinado(client, body, token_themembers)
    assert r.status_code == 200
    assert r.json()["status"] == "processado"

    await db.refresh(empresa)
    assert empresa.status_assinatura == "ativa"
    assert empresa.oferta_comercial == "profissional_mensal"


@pytest.mark.parametrize("produto_id,oferta_esperada", [
    ("prod-mensal-001", "profissional_mensal"),
    ("prod-semestral-002", "profissional_semestral"),
    ("prod-premium-003", "premium"),
])
async def test_6_mapeamento_produto_para_oferta(
    client, token_themembers, empresa_factory, usuario_factory, db, produto_id, oferta_esperada,
):
    empresa = await empresa_factory(status_assinatura="trial")
    email = f"prod-{produto_id}@teste.local"
    await usuario_factory(empresa, email=email)
    body = payload_direto("release.access", {"customer": {"email": email}, "product": {"id": produto_id}})
    r = await post_assinado(client, body, token_themembers)
    assert r.status_code == 200

    await db.refresh(empresa)
    assert empresa.oferta_comercial == oferta_esperada


async def test_7_produto_desconhecido_nao_ativa(client, token_themembers, empresa_factory, usuario_factory, db):
    empresa = await empresa_factory(status_assinatura="trial")
    await usuario_factory(empresa, email="desconhecido7@teste.local")
    body = payload_direto("release.access", {
        "customer": {"email": "desconhecido7@teste.local"}, "product": {"id": "produto-nao-cadastrado"},
    })
    r = await post_assinado(client, body, token_themembers)
    assert r.status_code == 200
    assert r.json()["status"] == "produto_desconhecido"

    await db.refresh(empresa)
    assert empresa.status_assinatura == "trial"  # não mudou


# ── 8-9: idempotência ─────────────────────────────────────────────────────────

async def test_8_evento_duplicado_nao_repete_mutacao(client, token_themembers, empresa_factory, usuario_factory, db):
    empresa = await empresa_factory(status_assinatura="trial")
    await usuario_factory(empresa, email="dup8@teste.local")
    body = payload_envelope("release.access", {
        "customer": {"email": "dup8@teste.local"}, "product": {"id": "prod-mensal-001"},
    }, id_="evt-dup-8")

    r1 = await post_assinado(client, body, token_themembers)
    r2 = await post_assinado(client, body, token_themembers)
    assert r1.status_code == 200
    assert r2.status_code == 200

    async with SessionLocal() as s:
        result = await s.execute(
            select(WebhookCheckoutEvento).where(WebhookCheckoutEvento.chave_evento == "release.access:evt-dup-8")
        )
        registros = result.scalars().all()
    assert len(registros) == 1


async def test_9_corrida_de_duplicados_contida_pela_constraint(empresa_factory, usuario_factory, token_themembers):
    empresa = await empresa_factory(status_assinatura="trial")
    await usuario_factory(empresa, email="corrida9@teste.local")
    body = payload_envelope("release.access", {
        "customer": {"email": "corrida9@teste.local"}, "product": {"id": "prod-mensal-001"},
    }, id_="evt-corrida-9")
    corpo_bruto = b'{"corrida": true}'

    async def _chamar():
        async with SessionLocal() as s:
            registro = await processar_webhook(s, body, corpo_bruto)
            await s.commit()
            return registro

    resultados = await asyncio.gather(_chamar(), _chamar())
    assert resultados[0].id == resultados[1].id or resultados[0].chave_evento == resultados[1].chave_evento

    async with SessionLocal() as s:
        result = await s.execute(
            select(WebhookCheckoutEvento).where(WebhookCheckoutEvento.chave_evento == "release.access:evt-corrida-9")
        )
        registros = result.scalars().all()
    assert len(registros) == 1


# ── 10-12: associação por e-mail ──────────────────────────────────────────────

async def test_10_email_associado_sem_diferenca_maiusculas(client, token_themembers, empresa_factory, usuario_factory, db):
    empresa = await empresa_factory(status_assinatura="trial")
    await usuario_factory(empresa, email="MaiUscula10@Teste.local")
    body = payload_direto("release.access", {
        "customer": {"email": "maiuscula10@teste.local"}, "product": {"id": "prod-mensal-001"},
    })
    r = await post_assinado(client, body, token_themembers)
    assert r.status_code == 200
    assert r.json()["status"] == "processado"
    await db.refresh(empresa)
    assert empresa.status_assinatura == "ativa"


async def test_10b_nao_quebra_com_contas_case_variante_duplicadas(client, token_themembers, empresa_factory, usuario_factory, db):
    """Achado na revisão de código: Usuario.email é único só case-sensitive no
    banco — duas contas "User@x.com"/"user@x.com" já existentes (de antes do
    fix no dedup de registrar_usuario, ou inseridas por outro caminho) faziam
    buscar_usuario_por_email quebrar com MultipleResultsFound. Usa
    usuario_factory pra simular o par já existente direto no banco (sem passar
    por registrar_usuario, que agora bloqueia isso na criação)."""
    empresa1 = await empresa_factory(status_assinatura="trial")
    empresa2 = await empresa_factory(status_assinatura="trial")
    await usuario_factory(empresa1, email="Duplicado10b@Teste.local")
    await usuario_factory(empresa2, email="duplicado10b@teste.local")

    body = payload_direto("release.access", {
        "customer": {"email": "duplicado10b@teste.local"}, "product": {"id": "prod-mensal-001"},
    })
    r = await post_assinado(client, body, token_themembers)
    assert r.status_code == 200
    assert r.json()["status"] == "processado"  # não 500 — não quebrou


async def test_10c_registrar_usuario_rejeita_email_case_variante(empresa_factory, usuario_factory, db):
    """Outra metade do fix 10b: registrar_usuario agora nega um cadastro novo
    que só difere na capitalização de um e-mail já existente, fechando a
    origem do par que causava o crash em buscar_usuario_por_email."""
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario

    empresa = await empresa_factory(status_assinatura="trial")
    await usuario_factory(empresa, email="jacadastrado10c@example.com")

    payload = UserCreate(
        username="novo10c",
        email="JaCadastrado10c@Example.com",
        password="senha123456",
        telefone="11999999999",
    )
    try:
        with pytest.raises(HTTPException) as exc:
            await registrar_usuario(payload, db)
        assert exc.value.status_code == 400
    finally:
        # Rede de segurança: se o dedup não bloqueasse (bug), registrar_usuario
        # teria commitado uma empresa+usuario novos que a fixture não conhece.
        await db.execute(delete(Usuario).where(Usuario.username == "novo10c"))
        orfa = await db.execute(select(Empresa).where(Empresa.nome == "novo10c"))
        empresa_orfa = orfa.scalar_one_or_none()
        if empresa_orfa:
            await db.execute(delete(Empresa).where(Empresa.id == empresa_orfa.id))
        await db.commit()


async def test_11_comprador_sem_conta_fica_pendente(client, token_themembers, db):
    body = payload_direto("release.access", {
        "customer": {"email": "nao-tem-conta-11@teste.local"}, "product": {"id": "prod-mensal-001"},
    })
    r = await post_assinado(client, body, token_themembers)
    assert r.status_code == 200
    assert r.json()["status"] == "pendente_usuario"

    # Sem empresa vinculada — nada pra empresa_factory limpar. Remove pelo e-mail.
    await db.execute(delete(WebhookCheckoutEvento).where(
        WebhookCheckoutEvento.email_comprador_normalizado == "nao-tem-conta-11@teste.local"
    ))
    await db.commit()


async def test_12_verificacao_email_reconcilia_pendencia(client, token_themembers, empresa_factory, usuario_factory, db):
    empresa = await empresa_factory(status_assinatura="trial")
    email = "reconciliar12@teste.local"

    # Compra chega ANTES da conta existir — fica pendente.
    body = payload_direto("release.access", {"customer": {"email": email}, "product": {"id": "prod-mensal-001"}})
    r = await post_assinado(client, body, token_themembers)
    assert r.json()["status"] == "pendente_usuario"

    # Conta criada depois, com o mesmo e-mail, ainda não verificada.
    usuario = await usuario_factory(empresa, email=email)
    usuario.email_verified = False
    usuario.email_verification_token = "token-verificacao-12"
    await db.commit()

    await verificar_email("token-verificacao-12", db)

    await db.refresh(empresa)
    assert empresa.status_assinatura == "ativa"
    assert empresa.oferta_comercial == "profissional_mensal"


# ── 13-15: revogação, precedência ─────────────────────────────────────────────

@pytest.mark.parametrize("evento,status_esperado", [
    ("revoke.access", "cancelada"),
    ("transaction.refunded", "cancelada"),
    ("transaction.charged_back", "suspensa"),
])
async def test_13_eventos_negativos_bloqueiam_escrita(
    client, token_themembers, empresa_factory, usuario_factory, db, evento, status_esperado,
):
    empresa = await empresa_factory(status_assinatura="ativa", oferta_comercial="profissional_mensal",
                                     assinatura_fim=date.today() + timedelta(days=20))
    email = f"negativo13-{evento}@teste.local"
    await usuario_factory(empresa, email=email)
    body = payload_direto(evento, {"customer": {"email": email}})
    r = await post_assinado(client, body, token_themembers)
    assert r.status_code == 200

    await db.refresh(empresa)
    assert empresa.status_assinatura == status_esperado
    with pytest.raises(HTTPException) as exc:
        await exigir_pode_editar(empresa_id=empresa.id, db=db)
    assert exc.value.status_code == 403


async def test_14_transaction_failed_nao_bloqueia_acesso_ja_pago(client, token_themembers, empresa_factory, usuario_factory, db):
    empresa = await empresa_factory(status_assinatura="ativa", oferta_comercial="profissional_mensal",
                                     assinatura_fim=date.today() + timedelta(days=20))
    email = "falhou14@teste.local"
    await usuario_factory(empresa, email=email)
    body = payload_direto("transaction.failed", {"customer": {"email": email}})
    r = await post_assinado(client, body, token_themembers)
    assert r.status_code == 200

    await db.refresh(empresa)
    assert empresa.status_assinatura == "ativa"
    # Não levanta — acesso continua liberado.
    await exigir_pode_editar(empresa_id=empresa.id, db=db)


async def test_15_evento_antigo_nao_reativa_assinatura_cancelada(client, token_themembers, empresa_factory, usuario_factory, db):
    empresa = await empresa_factory(status_assinatura="ativa", oferta_comercial="profissional_mensal")
    email = "precedencia15@teste.local"
    await usuario_factory(empresa, email=email)

    agora = datetime.now(timezone.utc)
    mais_recente = agora.isoformat()
    mais_antigo = (agora - timedelta(days=5)).isoformat()

    # Cancela com timestamp recente.
    body_cancelar = payload_direto("revoke.access", {"customer": {"email": email}}, created_at=mais_recente)
    r1 = await post_assinado(client, body_cancelar, token_themembers)
    assert r1.status_code == 200
    await db.refresh(empresa)
    assert empresa.status_assinatura == "cancelada"

    # Evento de ativação mais antigo chega depois — não pode reativar.
    body_antigo = payload_envelope("release.access", {
        "customer": {"email": email}, "product": {"id": "prod-mensal-001"},
    }, id_="evt-antigo-15")
    body_antigo["payload"]["created_at"] = mais_antigo
    r2 = await post_assinado(client, body_antigo, token_themembers)
    assert r2.status_code == 200
    assert r2.json()["status"] == "ignorado"

    await db.refresh(empresa)
    assert empresa.status_assinatura == "cancelada"


async def test_15b_revoke_antigo_nao_cancela_ativacao_mais_nova(client, token_themembers, empresa_factory, usuario_factory, db):
    """Direção simétrica do teste 15, achada na revisão de código: revoke.access
    aplicava incondicionalmente (sem checar _pode_aplicar), então um revoke
    atrasado podia cancelar uma assinatura já renovada por um evento mais novo."""
    empresa = await empresa_factory(status_assinatura="trial")
    email = "precedencia15b@teste.local"
    await usuario_factory(empresa, email=email)

    agora = datetime.now(timezone.utc)
    mais_antigo = (agora - timedelta(days=5)).isoformat()
    mais_recente = agora.isoformat()

    # Ativa com timestamp recente.
    body_ativar = payload_envelope("release.access", {
        "customer": {"email": email}, "product": {"id": "prod-mensal-001"},
    }, id_="evt-ativar-15b")
    body_ativar["payload"]["created_at"] = mais_recente
    r1 = await post_assinado(client, body_ativar, token_themembers)
    assert r1.status_code == 200
    await db.refresh(empresa)
    assert empresa.status_assinatura == "ativa"

    # Revoke mais antigo chega depois — não pode cancelar a ativação mais nova.
    body_revoke_antigo = payload_direto("revoke.access", {"customer": {"email": email}}, created_at=mais_antigo)
    r2 = await post_assinado(client, body_revoke_antigo, token_themembers)
    assert r2.status_code == 200
    assert r2.json()["status"] == "ignorado"

    await db.refresh(empresa)
    assert empresa.status_assinatura == "ativa"


# ── 16-17: robustez de payload ────────────────────────────────────────────────

def test_16_ids_numericos_grandes_preservados_como_string():
    body = payload_envelope(
        "transaction.approved", {"customer": {"email": "id-grande16@teste.local"}}, id_=7501283916486672384,
    )
    evento = normalizar_payload(body)
    assert evento.external_id == "7501283916486672384"
    assert isinstance(evento.external_id, str)


async def test_17_campos_opcionais_null_nao_derrubam_endpoint(client, token_themembers, db):
    body = payload_direto("transaction.approved", {
        "customer": None, "product": None, "subscription": None, "order": None,
    })
    r = await post_assinado(client, body, token_themembers)
    assert r.status_code == 200

    # Sem e-mail identificável -> ignorado, sem empresa vinculada pra empresa_factory limpar.
    await db.execute(delete(WebhookCheckoutEvento).where(
        WebhookCheckoutEvento.status_processamento == "ignorado",
        WebhookCheckoutEvento.email_comprador_normalizado.is_(None),
    ))
    await db.commit()


# ── 18-20: regra de bloqueio de edição ────────────────────────────────────────

async def test_18_trial_vencido_continua_bloqueado(empresa_factory, db):
    empresa = await empresa_factory(status_assinatura="trial", assinatura_fim=date.today() - timedelta(days=1))
    with pytest.raises(HTTPException) as exc:
        await exigir_pode_editar(empresa_id=empresa.id, db=db)
    assert exc.value.status_code == 403


async def test_19_conta_ativa_expirada_passa_a_bloquear(empresa_factory, db):
    empresa = await empresa_factory(status_assinatura="ativa", assinatura_fim=date.today() - timedelta(days=1))
    with pytest.raises(HTTPException) as exc:
        await exigir_pode_editar(empresa_id=empresa.id, db=db)
    assert exc.value.status_code == 403


async def test_20_conta_legada_ativa_com_fim_null_permanece_utilizavel(empresa_factory, db):
    empresa = await empresa_factory(status_assinatura="ativa", assinatura_fim=None)
    await exigir_pode_editar(empresa_id=empresa.id, db=db)  # não levanta


# ── 21: falha transitória ─────────────────────────────────────────────────────

async def test_21_falha_de_banco_retorna_500_sem_marcar_processado(client, token_themembers, monkeypatch):
    import app.services.webhook_themembers as mod

    async def _explode(*args, **kwargs):
        raise RuntimeError("falha simulada de banco/processamento")

    monkeypatch.setattr(mod, "_processar_evento_novo", _explode)

    body = payload_envelope("release.access", {
        "customer": {"email": "falha21@teste.local"}, "product": {"id": "prod-mensal-001"},
    }, id_="evt-falha-21")
    r = await post_assinado(client, body, token_themembers)
    assert r.status_code == 500

    async with SessionLocal() as s:
        result = await s.execute(
            select(WebhookCheckoutEvento).where(WebhookCheckoutEvento.chave_evento == "release.access:evt-falha-21")
        )
        assert result.scalar_one_or_none() is None


# ── 22: higiene de log ─────────────────────────────────────────────────────────

async def test_22_logs_nao_contem_token_nem_payload_integral(client, token_themembers, empresa_factory, usuario_factory, caplog):
    empresa = await empresa_factory(status_assinatura="trial")
    email = "logsensivel22@teste.local"
    await usuario_factory(empresa, email=email)

    with caplog.at_level("INFO", logger="app.services.webhook_themembers"):
        body = payload_direto("release.access", {
            "customer": {"email": email, "document": "123.456.789-00", "phone": "+55 11 99999-8888"},
            "product": {"id": "prod-mensal-001"},
        })
        r = await post_assinado(client, body, token_themembers)
        assert r.status_code == 200

    texto_logs = caplog.text
    assert token_themembers not in texto_logs
    assert "123.456.789-00" not in texto_logs
    assert "99999-8888" not in texto_logs
