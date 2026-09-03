"""Webhook do Checkout TheMembers/TheBank.

Implementa a especificação em
docs/handoffs/especificacao-webhook-checkout-themembers-2026-09-03.md.
Etapa 1: código completo, testado com fixtures baseadas na documentação
pública — ativação real em produção fica atrás de
`THEMEMBERS_WEBHOOK_ENABLED=false` até confirmar payload real de cada
produto (spec §18/§20).
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.assinatura_gateway import AssinaturaGateway
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.webhook_checkout_evento import (
    STATUS_ERRO,
    STATUS_IGNORADO,
    STATUS_PENDENTE_USUARIO,
    STATUS_PROCESSADO,
    STATUS_PRODUTO_DESCONHECIDO,
    STATUS_RECEBIDO,
    WebhookCheckoutEvento,
)
from app.schemas.webhook_themembers import EventoNormalizado

logger = logging.getLogger(__name__)

# Eventos que ativam ou renovam acesso.
EVENTOS_ATIVACAO = {"release.access"}
EVENTOS_PAGAMENTO = {"transaction.approved"}
# Eventos que revogam/bloqueiam acesso de escrita — sempre prevalecem sobre
# uma aprovação anterior da mesma empresa (spec §11, regra de precedência).
EVENTOS_REVOGACAO = {"revoke.access", "transaction.refunded"}
EVENTOS_SUSPENSAO = {"transaction.charged_back"}
# Só auditoria — não mudam estado de acesso.
EVENTOS_SOMENTE_AUDITORIA = {
    "transaction.failed",
    "transaction.pending_refund",
    "order.completed",
    "order.canceled",
    "order.expired",
    "abandoned",
}

OFERTA_POR_ENV_VAR = {
    "THEMEMBERS_PRODUCT_MONTHLY_ID": "profissional_mensal",
    "THEMEMBERS_PRODUCT_SEMIANNUAL_ID": "profissional_semestral",
    "THEMEMBERS_PRODUCT_PREMIUM_ID": "premium",
}


# ── Normalização do payload (spec §8) ───────────────────────────────────────

def normalizar_payload(body: dict[str, Any]) -> EventoNormalizado:
    """Aceita os 2 formatos de envelope documentados e devolve um formato
    estável. Campos ausentes/None nunca derrubam a normalização — tudo é
    Optional no schema de saída."""
    envelope = body
    payload_interno = body.get("payload") if isinstance(body, dict) else None
    if isinstance(payload_interno, dict) and "event" in payload_interno:
        envelope = payload_interno

    if not isinstance(envelope, dict) or "event" not in envelope:
        raise ValueError("Corpo do webhook não contém um evento reconhecível.")

    data = envelope.get("data") or {}
    if not isinstance(data, dict):
        data = {}

    email = (
        _buscar_aninhado(data, "customer", "email")
        or _buscar_aninhado(data, "subscription", "subscriber", "email")
        or _buscar_aninhado(data, "order", "customer", "email")
    )

    produto_id = _stringificar(
        _buscar_aninhado(data, "product", "id")
        or _buscar_aninhado(data, "product", "reference_id")
        or data.get("product_id")
    )

    return EventoNormalizado(
        event=str(envelope["event"]),
        objeto=_stringificar(envelope.get("object")),
        external_id=_stringificar(envelope.get("id") or data.get("id")),
        produto_id=produto_id,
        email_comprador=email.strip().lower() if isinstance(email, str) and email.strip() else None,
        data=data,
        criado_em_provedor=_parsear_data(envelope.get("created_at") or data.get("created_at")),
        proxima_cobranca_em=_parsear_data(_buscar_aninhado(data, "subscription", "next_billing_at")),
        expira_em=_parsear_data(_buscar_aninhado(data, "product", "expires_in")),
        external_customer_id=_stringificar(_buscar_aninhado(data, "customer", "id")),
        external_order_id=_stringificar(_buscar_aninhado(data, "order", "id")),
        external_subscription_code=_stringificar(_buscar_aninhado(data, "subscription", "id")),
    )


def _buscar_aninhado(obj: dict[str, Any], *chaves: str) -> Any:
    atual: Any = obj
    for chave in chaves:
        if not isinstance(atual, dict):
            return None
        atual = atual.get(chave)
    return atual


def _stringificar(valor: Any) -> Optional[str]:
    """IDs podem vir como número grande — sempre preservar como string,
    nunca deixar virar float (spec §6/teste 16)."""
    if valor is None:
        return None
    return str(valor)


def _parsear_data(valor: Any) -> Optional[datetime]:
    if not valor or not isinstance(valor, str):
        return None
    try:
        dt = datetime.fromisoformat(valor.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


# ── Idempotência (spec §9) ───────────────────────────────────────────────────

def construir_chave_evento(evento: EventoNormalizado, corpo_bruto: bytes) -> str:
    if evento.external_id:
        return f"{evento.event}:{evento.external_id}"
    data_id = evento.data.get("id") if isinstance(evento.data, dict) else None
    if data_id:
        return f"{evento.event}:{data_id}"
    digest = hashlib.sha256(corpo_bruto).hexdigest()
    return f"{evento.event}:sha256:{digest}"


# ── Mapeamento de produto → oferta comercial (spec §6/§11) ──────────────────

def mapear_oferta(produto_id: Optional[str]) -> Optional[str]:
    if not produto_id:
        return None
    for env_var, oferta in OFERTA_POR_ENV_VAR.items():
        configurado = getattr(settings, env_var, "")
        if configurado and produto_id == configurado:
            return oferta
    return None


# ── Associação do comprador por e-mail (spec §10) ────────────────────────────

async def buscar_usuario_por_email(db: AsyncSession, email_normalizado: str) -> Optional[Usuario]:
    # Achado na revisão de código: Usuario.email é único só de forma
    # case-sensitive no banco (e no dedup de registrar_usuario) — duas contas
    # "User@x.com"/"user@x.com" podem coexistir. Essa busca é case-insensitive
    # de propósito (o comprador pode digitar o e-mail com capitalização
    # diferente no checkout), então usa .limit(1) em vez de
    # scalar_one_or_none() pra nunca quebrar com MultipleResultsFound caso
    # esse par exista — pega a conta mais antiga, que é a decisão razoável.
    result = await db.execute(
        select(Usuario)
        .where(func.lower(Usuario.email) == email_normalizado)
        .order_by(Usuario.created_at.asc())
        .limit(1)
    )
    return result.scalars().first()


# ── Processamento principal ──────────────────────────────────────────────────

async def processar_webhook(
    db: AsyncSession,
    body: dict[str, Any],
    corpo_bruto: bytes,
) -> WebhookCheckoutEvento:
    """Ponto de entrada chamado pela rota, já com o token validado.
    Levanta ValueError se o JSON não tiver um formato reconhecível (a rota
    converte isso em 400/422). Qualquer outra exceção não tratada aqui
    propaga (a rota converte em 500 — nada fica marcado como processado
    nesse caso, permitindo retry seguro do provedor)."""
    evento = normalizar_payload(body)
    chave = construir_chave_evento(evento, corpo_bruto)

    existente = await db.execute(
        select(WebhookCheckoutEvento).where(WebhookCheckoutEvento.chave_evento == chave)
    )
    registro_existente = existente.scalar_one_or_none()
    if registro_existente is not None:
        # Idempotente — evento já visto antes, nunca reprocessa cegamente
        # (spec §9). Reprocessamento de um evento em erro é manual/admin,
        # não automático dentro do próprio webhook.
        return registro_existente

    registro = WebhookCheckoutEvento(
        provedor="themembers",
        chave_evento=chave,
        tipo_evento=evento.event,
        objeto=evento.objeto,
        external_id=evento.external_id,
        produto_id=evento.produto_id,
        email_comprador_normalizado=evento.email_comprador,
        status_processamento=STATUS_RECEBIDO,
        payload=body,
        recebido_em=datetime.now(timezone.utc),
    )
    db.add(registro)
    try:
        await db.flush()
    except IntegrityError:
        # Corrida entre 2 entregas simultâneas — a constraint única pegou
        # antes de nós (spec §9, teste 9). Devolve o registro que "ganhou".
        await db.rollback()
        existente2 = await db.execute(
            select(WebhookCheckoutEvento).where(WebhookCheckoutEvento.chave_evento == chave)
        )
        return existente2.scalar_one()

    await _processar_evento_novo(db, registro, evento)
    registro.processado_em = datetime.now(timezone.utc)
    await db.flush()

    # Log estruturado (spec §17) — nunca token, PII completa ou payload
    # integral (spec §2/§7.2, teste 22).
    logger.info(
        "webhook_checkout chave=%s tipo=%s produto=%s empresa_id=%s status=%s",
        registro.chave_evento, registro.tipo_evento, registro.produto_id,
        registro.empresa_id, registro.status_processamento,
    )
    return registro


async def _processar_evento_novo(
    db: AsyncSession,
    registro: WebhookCheckoutEvento,
    evento: EventoNormalizado,
) -> None:
    if not evento.email_comprador:
        registro.status_processamento = STATUS_IGNORADO
        registro.erro_resumido = "Evento sem e-mail de comprador identificável."
        return

    usuario = await buscar_usuario_por_email(db, evento.email_comprador)
    if usuario is None:
        registro.status_processamento = STATUS_PENDENTE_USUARIO
        return

    registro.empresa_id = usuario.empresa_id
    await _aplicar_efeito(db, evento, registro, usuario.empresa_id)


async def _aplicar_efeito(
    db: AsyncSession,
    evento: EventoNormalizado,
    registro: WebhookCheckoutEvento,
    empresa_id: UUID,
) -> None:
    empresa = await db.get(Empresa, empresa_id)
    if empresa is None:
        registro.status_processamento = STATUS_ERRO
        registro.erro_resumido = "Empresa do usuário associado não foi encontrada."
        return

    gateway = await _obter_ou_criar_gateway(db, empresa_id)
    timestamp_evento = evento.criado_em_provedor or datetime.now(timezone.utc)

    if evento.event in EVENTOS_REVOGACAO or evento.event in EVENTOS_SUSPENSAO:
        # Achado na revisão de código: revogação aplicava incondicionalmente,
        # sem checar _pode_aplicar como a ativação — um revoke.access atrasado
        # (ex: redelivery de uma compra já superada) podia cancelar uma
        # assinatura mais nova e legítima. "Refund/chargeback/revoke sempre
        # prevalece sobre aprovação ANTERIOR" (spec §11) já significa "quando
        # o revoke é o evento mais novo" — é exatamente o que _pode_aplicar
        # already checa, então a checagem é simétrica com a ativação agora.
        if not _pode_aplicar(gateway, timestamp_evento):
            registro.status_processamento = STATUS_IGNORADO
            registro.erro_resumido = "Evento mais antigo que o último já aplicado para esta assinatura."
            return
        empresa.status_assinatura = "cancelada" if evento.event in EVENTOS_REVOGACAO else "suspensa"
        _registrar_evento_aplicado(gateway, evento, timestamp_evento, forcar=True)
        registro.status_processamento = STATUS_PROCESSADO
        return

    if evento.event in EVENTOS_SOMENTE_AUDITORIA:
        registro.status_processamento = STATUS_PROCESSADO
        return

    if evento.event in EVENTOS_ATIVACAO or evento.event in EVENTOS_PAGAMENTO:
        oferta = mapear_oferta(evento.produto_id)
        if oferta is None:
            if evento.event in EVENTOS_PAGAMENTO:
                # transaction.approved sem produto mapeado só registra o
                # pagamento — não é erro, não ativa nada (spec §11).
                gateway.ultimo_pagamento_em = timestamp_evento
                registro.status_processamento = STATUS_PROCESSADO
                return
            registro.status_processamento = STATUS_PRODUTO_DESCONHECIDO
            registro.erro_resumido = f"produto_id não mapeado: {evento.produto_id!r}"
            return

        if not _pode_aplicar(gateway, timestamp_evento):
            # Evento cronologicamente mais antigo que o último já aplicado —
            # não reativa por cima de um cancelamento mais recente (spec §11).
            registro.status_processamento = STATUS_IGNORADO
            registro.erro_resumido = "Evento mais antigo que o último já aplicado para esta assinatura."
            return

        empresa.status_assinatura = "ativa"
        empresa.oferta_comercial = oferta
        if evento.expira_em is not None:
            empresa.assinatura_fim = evento.expira_em.date()
        elif oferta == "profissional_mensal" and evento.proxima_cobranca_em is not None:
            empresa.assinatura_fim = evento.proxima_cobranca_em.date()
        # Semestral/Premium sem expires_in no payload: não inventa "180 dias"
        # (spec §12) — assinatura_fim fica como estava até confirmar a regra
        # com payload real.

        gateway.external_product_id = evento.produto_id
        gateway.external_customer_id = evento.external_customer_id or gateway.external_customer_id
        gateway.external_order_id = evento.external_order_id or gateway.external_order_id
        gateway.external_subscription_code = evento.external_subscription_code or gateway.external_subscription_code
        gateway.status_gateway = evento.event
        if evento.proxima_cobranca_em is not None:
            gateway.proxima_cobranca_em = evento.proxima_cobranca_em.date()
        if evento.event in EVENTOS_PAGAMENTO:
            gateway.ultimo_pagamento_em = timestamp_evento
        _registrar_evento_aplicado(gateway, evento, timestamp_evento, forcar=False)
        registro.status_processamento = STATUS_PROCESSADO
        return

    # Evento reconhecido pelo normalizador mas fora do mapeamento conhecido —
    # audita sem alterar nada, não é erro de processamento.
    registro.status_processamento = STATUS_IGNORADO


def _pode_aplicar(gateway: AssinaturaGateway, timestamp_evento: datetime) -> bool:
    if gateway.ultimo_evento_aplicado_em is None:
        return True
    referencia = gateway.ultimo_evento_aplicado_em
    if referencia.tzinfo is None:
        referencia = referencia.replace(tzinfo=timezone.utc)
    return timestamp_evento >= referencia


def _registrar_evento_aplicado(
    gateway: AssinaturaGateway,
    evento: EventoNormalizado,
    timestamp_evento: datetime,
    forcar: bool,
) -> None:
    if forcar or _pode_aplicar(gateway, timestamp_evento):
        referencia_atual = gateway.ultimo_evento_aplicado_em
        if referencia_atual is None or timestamp_evento > (
            referencia_atual if referencia_atual.tzinfo else referencia_atual.replace(tzinfo=timezone.utc)
        ):
            gateway.ultimo_evento_aplicado_em = timestamp_evento


async def _obter_ou_criar_gateway(db: AsyncSession, empresa_id: UUID) -> AssinaturaGateway:
    result = await db.execute(
        select(AssinaturaGateway).where(
            AssinaturaGateway.empresa_id == empresa_id,
            AssinaturaGateway.provedor == "themembers",
        )
    )
    gateway = result.scalar_one_or_none()
    if gateway is not None:
        return gateway

    gateway = AssinaturaGateway(empresa_id=empresa_id, provedor="themembers")
    try:
        # SAVEPOINT (não rollback da sessão inteira): quando chegamos aqui já
        # existe outro trabalho não commitado na mesma transação (o
        # WebhookCheckoutEvento gravado antes, em processar_webhook) — um
        # db.rollback() cheio, como o padrão usado lá, perderia esse registro
        # também. begin_nested() desfaz só esta tentativa de insert.
        async with db.begin_nested():
            db.add(gateway)
            await db.flush()
    except IntegrityError:
        # Corrida entre 2 webhooks quase simultâneos pra mesma empresa (ex:
        # release.access + transaction.approved da mesma compra) — a
        # constraint única (uq_assinatura_gateway_empresa_provedor, achada na
        # revisão de código) pegou antes de nós.
        existente = await db.execute(
            select(AssinaturaGateway).where(
                AssinaturaGateway.empresa_id == empresa_id,
                AssinaturaGateway.provedor == "themembers",
            )
        )
        gateway = existente.scalar_one()
    return gateway


# ── Reconciliação após verificação de e-mail (spec §10) ─────────────────────

async def reconciliar_pendencias_email(db: AsyncSession, usuario: Usuario) -> int:
    """Chamado depois que o usuário verifica o e-mail — processa em ordem
    cronológica todo evento que ficou `pendente_usuario` com o mesmo e-mail.
    Devolve quantos eventos foram reconciliados."""
    email_normalizado = usuario.email.strip().lower()
    result = await db.execute(
        select(WebhookCheckoutEvento)
        .where(
            WebhookCheckoutEvento.email_comprador_normalizado == email_normalizado,
            WebhookCheckoutEvento.status_processamento == STATUS_PENDENTE_USUARIO,
        )
        .order_by(WebhookCheckoutEvento.recebido_em.asc())
    )
    pendentes = result.scalars().all()
    for registro in pendentes:
        # Achado na revisão de código: reconstruir o EventoNormalizado à mão
        # (em vez de reusar normalizar_payload) deixava expira_em/
        # proxima_cobranca_em/external_*_id de fora — a empresa ativava sem
        # nunca gravar validade. Reusar o mesmo normalizador do caminho ao
        # vivo garante os mesmos campos e usa o created_at real do provedor
        # (não o horário em que recebemos o evento) pra precedência.
        evento = normalizar_payload(registro.payload)
        registro.empresa_id = usuario.empresa_id
        await _aplicar_efeito(db, evento, registro, usuario.empresa_id)
        registro.processado_em = datetime.now(timezone.utc)
    if pendentes:
        await db.flush()
    return len(pendentes)
