"""Webhook do Checkout TheMembers — tabelas de evento/assinatura + oferta_comercial

Etapa 1 da especificação em
docs/handoffs/especificacao-webhook-checkout-themembers-2026-09-03.md —
só schema. O endpoint fica desabilitado (`THEMEMBERS_WEBHOOK_ENABLED=false`)
até confirmar payload real de cada produto antes de ativar de verdade (§18
da spec).

`oferta_comercial` é um eixo comercial independente de `empresa.plano`
(que continua só técnico/empresa, nunca um rótulo comercial — ver
docs/decisoes/2026-08-30-plano-x-status.md). Backfill: toda empresa em
trial vira `avaliacao`; contas ativas legadas ficam `NULL` de propósito
(não tem como inferir qual oferta paga sem dado real do gateway).

Revision ID: 0036
Revises: 0035
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

revision = "0036"
down_revision = "0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("empresa", sa.Column("oferta_comercial", sa.String(30), nullable=True))
    op.execute("UPDATE empresa SET oferta_comercial = 'avaliacao' WHERE status_assinatura = 'trial'")

    op.create_table(
        "webhook_checkout_evento",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("provedor", sa.String(30), nullable=False, server_default="themembers"),
        sa.Column("chave_evento", sa.String(300), nullable=False),
        sa.Column("tipo_evento", sa.String(100), nullable=False),
        sa.Column("objeto", sa.String(50), nullable=True),
        sa.Column("external_id", sa.String(150), nullable=True),
        sa.Column("produto_id", sa.String(150), nullable=True),
        sa.Column("email_comprador_normalizado", sa.String(200), nullable=True),
        sa.Column("empresa_id", pg.UUID(as_uuid=True), sa.ForeignKey("empresa.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status_processamento", sa.String(30), nullable=False, server_default="recebido"),
        sa.Column("erro_resumido", sa.String(500), nullable=True),
        sa.Column("payload", pg.JSONB(), nullable=False),
        sa.Column("recebido_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("chave_evento", name="uq_webhook_checkout_evento_chave"),
    )
    op.create_index("ix_webhook_checkout_evento_empresa_id", "webhook_checkout_evento", ["empresa_id"])
    op.create_index("ix_webhook_checkout_evento_email", "webhook_checkout_evento", ["email_comprador_normalizado"])
    op.create_index("ix_webhook_checkout_evento_status", "webhook_checkout_evento", ["status_processamento"])

    op.create_table(
        "assinatura_gateway",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", pg.UUID(as_uuid=True), sa.ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provedor", sa.String(30), nullable=False, server_default="themembers"),
        sa.Column("external_customer_id", sa.String(150), nullable=True),
        sa.Column("external_product_id", sa.String(150), nullable=True),
        sa.Column("external_order_id", sa.String(150), nullable=True),
        sa.Column("external_subscription_code", sa.String(150), nullable=True),
        sa.Column("status_gateway", sa.String(50), nullable=True),
        sa.Column("proxima_cobranca_em", sa.Date(), nullable=True),
        sa.Column("ultimo_pagamento_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultimo_evento_aplicado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_assinatura_gateway_empresa_id", "assinatura_gateway", ["empresa_id"])


def downgrade() -> None:
    op.drop_index("ix_assinatura_gateway_empresa_id", table_name="assinatura_gateway")
    op.drop_table("assinatura_gateway")

    op.drop_index("ix_webhook_checkout_evento_status", table_name="webhook_checkout_evento")
    op.drop_index("ix_webhook_checkout_evento_email", table_name="webhook_checkout_evento")
    op.drop_index("ix_webhook_checkout_evento_empresa_id", table_name="webhook_checkout_evento")
    op.drop_table("webhook_checkout_evento")

    op.drop_column("empresa", "oferta_comercial")
