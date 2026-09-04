from datetime import date
from uuid import UUID, uuid4
from typing import List, Optional

from sqlalchemy import String, Date, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

# Papéis de usuário
PAPEL_SUPERADMIN = "superadmin_icenexus"   # equipe IceNexus — cura catálogo, acessa cross-empresa
PAPEL_ADMIN = "admin_empresa"              # administra a própria empresa
PAPEL_MEMBRO = "membro"                    # usa o app dentro da empresa

# Status de assinatura que liberam o uso
STATUS_ATIVOS = ("ativa", "trial")

# Trial gratuito: DESIGN_TRIAL_15_DIAS — decisão de 2026-08-25. 15 dias, 1
# projeto; vencido o prazo, o projeto continua visível/exportável, só não
# edita mais (ver Empresa.trial_expirado).
DURACAO_TRIAL_DIAS = 15
LIMITE_PROJETOS_TRIAL = 1


class Empresa(Base, TimestampMixin):
    """Tenant. Todo dado de projeto/cliente/cotação é escopado por empresa."""

    __tablename__ = "empresa"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    cnpj: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    plano: Mapped[str] = mapped_column(String(30), default="tecnico", server_default="tecnico")
    status_assinatura: Mapped[str] = mapped_column(String(20), default="ativa", server_default="ativa")
    assinatura_inicio: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    assinatura_fim: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # Eixo comercial independente de `plano` (que é só técnico/empresa) — identifica
    # a oferta paga (avaliacao/profissional_mensal/profissional_semestral/premium),
    # ver docs/decisoes/2026-08-30-plano-x-status.md e o handoff do webhook TheMembers.
    oferta_comercial: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Recursos avançados (Classificação de Itens, Catálogo de Preços) — nascem
    # desligados pra todo mundo (técnico ou empresa); só o superadmin liga por
    # exceção, no painel de Administração. Só esconde o menu no frontend — de
    # propósito sem gate no backend, pra não arriscar nada nas rotas já em uso.
    recursos_avancados_habilitados: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    # Identidade da proposta ao cliente (Card 6) — editável por qualquer membro
    # (não é área sensível de conta, é o próprio técnico personalizando o que
    # entrega pro próprio cliente). `proposta_nome` é independente de `nome`
    # de propósito — não abre edição do nome oficial da conta pra qualquer membro.
    proposta_nome: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    proposta_logo_base64: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposta_contato_nome: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    proposta_contato_telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    usuarios: Mapped[List["Usuario"]] = relationship(back_populates="empresa")

    @property
    def ativa(self) -> bool:
        return self.status_assinatura in STATUS_ATIVOS

    @property
    def trial_expirado(self) -> bool:
        """True só quando o trial venceu — bloqueia edição, não leitura/exportação.

        `plano` (técnico/empresa) é só o produto contratado — nunca vale
        "trial". "Trial" é exclusivamente um `status_assinatura`, a fase
        temporária de qualquer produto antes da assinatura ser confirmada.

        `assinatura_fim is None` nunca expira (cobre empresas criadas antes
        desta checagem existir, que não têm data gravada — não são
        retroativamente trancadas por uma mudança de código).
        """
        return (
            self.status_assinatura == "trial"
            and self.assinatura_fim is not None
            and self.assinatura_fim < date.today()
        )
