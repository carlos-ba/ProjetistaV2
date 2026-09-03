from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

# Status de processamento de um evento de webhook — ver
# docs/handoffs/especificacao-webhook-checkout-themembers-2026-09-03.md §7.2
STATUS_RECEBIDO = "recebido"
STATUS_PROCESSADO = "processado"
STATUS_PENDENTE_USUARIO = "pendente_usuario"
STATUS_PRODUTO_DESCONHECIDO = "produto_desconhecido"
STATUS_IGNORADO = "ignorado"
STATUS_ERRO = "erro"


class WebhookCheckoutEvento(Base, TimestampMixin):
    """Idempotência + auditoria de todo evento recebido do Checkout do provedor
    de pagamento. `payload` guarda o corpo original (PII) — acesso restrito a
    banco/admin técnico, nunca deve ser espelhado em log de aplicação comum.
    """

    __tablename__ = "webhook_checkout_evento"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    provedor: Mapped[str] = mapped_column(String(30), nullable=False, default="themembers")
    chave_evento: Mapped[str] = mapped_column(String(300), unique=True, nullable=False)
    tipo_evento: Mapped[str] = mapped_column(String(100), nullable=False)
    objeto: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    produto_id: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    email_comprador_normalizado: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    empresa_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("empresa.id", ondelete="SET NULL"), nullable=True
    )
    status_processamento: Mapped[str] = mapped_column(String(30), nullable=False, default=STATUS_RECEBIDO)
    erro_resumido: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    recebido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processado_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
