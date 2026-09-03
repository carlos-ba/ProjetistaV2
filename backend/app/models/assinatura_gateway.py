from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, ForeignKey, Date, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AssinaturaGateway(Base, TimestampMixin):
    """Vínculo atual da assinatura de uma empresa com o provedor de pagamento —
    histórico de referências externas, separado da projeção rápida que o
    produto usa (`Empresa.status_assinatura`/`oferta_comercial`/`assinatura_fim`).
    Permite trocar de oferta sem perder o histórico anterior.
    """

    __tablename__ = "assinatura_gateway"
    __table_args__ = (
        UniqueConstraint("empresa_id", "provedor", name="uq_assinatura_gateway_empresa_provedor"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    empresa_id: Mapped[UUID] = mapped_column(
        ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    provedor: Mapped[str] = mapped_column(String(30), nullable=False, default="themembers")
    external_customer_id: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    external_product_id: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    external_order_id: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    external_subscription_code: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    status_gateway: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    proxima_cobranca_em: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ultimo_pagamento_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Timestamp do provedor referente ao último evento aplicado — usado pra
    # decidir precedência quando eventos chegam fora de ordem (ver
    # docs/handoffs/especificacao-webhook-checkout-themembers-2026-09-03.md §11).
    ultimo_evento_aplicado_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
