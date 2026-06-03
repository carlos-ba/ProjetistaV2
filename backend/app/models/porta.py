from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Numeric, ForeignKey, Integer, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PortaFrigoriifica(Base):
    """
    Catálogo de portas frigoríficas.

    Classificação:
      resfriados   → câmaras de 0°C a +10°C
      congelada    → câmaras de -15°C a -25°C
      ultra-congelada → abaixo de -25°C

    Tipo:
      giratoria    → dobradiças, abre em 90° ou 180°
      deslizante   → corre na parede (economiza espaço)
      rapida       → cortina ou porta de alta velocidade (operação frequente)

    A seleção é feita no Módulo 1 (Configuração do Gabinete).
    Uma câmara pode ter N portas com especificações diferentes.
    """
    __tablename__ = "porta_frigoriifica"

    id: Mapped[int]            = mapped_column(primary_key=True, autoincrement=True)
    fabricante_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fabricante.id"), nullable=True)

    descricao:     Mapped[str] = mapped_column(String(150), nullable=False)
    tipo:          Mapped[str] = mapped_column(String(30),  nullable=False)   # giratoria | deslizante | rapida
    largura_mm:    Mapped[int] = mapped_column(Integer,     nullable=False)
    altura_mm:     Mapped[int] = mapped_column(Integer,     nullable=False)
    espessura_mm:  Mapped[int] = mapped_column(Integer,     nullable=False)
    classificacao: Mapped[str] = mapped_column(String(30),  nullable=False)   # resfriados | congelada | ultra-congelada
    abertura:      Mapped[Optional[str]] = mapped_column(String(20), nullable=True)   # direita | esquerda | ambas | automatica
    batente:       Mapped[Optional[str]] = mapped_column(String(10), nullable=True)   # 3B | 4B
    soleira:       Mapped[bool]          = mapped_column(Boolean, default=False)
    custo:         Mapped[Decimal]       = mapped_column(Numeric(10, 2), default=0)
    observacao:    Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    fabricante: Mapped[Optional["Fabricante"]] = relationship()
