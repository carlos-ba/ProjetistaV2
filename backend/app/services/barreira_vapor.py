"""Barreira de vapor do piso (Card 1, piso convencional) — desmembrada em 3
itens reais (Lona Val Film, Fita Branca, Lona), resolvidos aqui por
dependerem do catálogo (banco), fora de calculos_gabinete.py (síncrono/sem
DB) — mesmo padrão de separação já usado pro kit de montagem.

Fórmulas confirmadas pelo usuário com quem elaborou a planilha de
referência (VALFIM), contra um projeto real de 134 m² de área de piso:
  - Lona Val Film: área x 1,20                              → m²
  - Fita Branca:   ceil((área x 1,20 / 223) x 1,50)          → rolos
  - Lona:          (área x 1,32) / 4                         → m

223 (rendimento m²/rolo da Fita Branca) e 1,50 (fator de segurança) ficam
fixos por decisão consciente — se um dia precisarem variar por projeto,
viram campo configurável (mesmo caminho já percorrido pelo
`rendimento_selante_m_por_embalagem` do kit de montagem).
"""
from __future__ import annotations
import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalogo_generico import CatalogoGenerico
from app.schemas.gabinete import MaterialExtra

RENDIMENTO_FITA_BRANCA_M2_POR_ROLO = 223.0
FATOR_SEGURANCA_FITA_BRANCA = 1.50


async def _buscar(db: AsyncSession, tipo_item: str) -> CatalogoGenerico | None:
    return (
        await db.execute(
            select(CatalogoGenerico)
            .where(CatalogoGenerico.tipo_item == tipo_item, CatalogoGenerico.ativo.is_(True))
            .order_by(CatalogoGenerico.id)
            .limit(1)
        )
    ).scalars().first()


async def calcular_barreira_vapor(
    db: AsyncSession, area_piso_m2: float,
) -> tuple[list[MaterialExtra], list[str]]:
    itens: list[MaterialExtra] = []
    avisos: list[str] = []
    if area_piso_m2 <= 0:
        return itens, avisos

    lona_val_film_m2 = area_piso_m2 * 1.20
    item = await _buscar(db, "lona_val_film")
    if not item:
        avisos.append("Nenhuma Lona Val Film cadastrada no catálogo — item não incluído na lista.")
    else:
        itens.append(MaterialExtra(
            item="Lona Val Film",
            qtd=f"{lona_val_film_m2:.2f} m²",
            quantidade=round(lona_val_film_m2, 2),
            unidade="m²",
            detalhe=f"{item.descricao} ({item.codigo_fabricante}) — área do piso x 1,20",
            tipo_item="lona_val_film",
        ))

    rolos_fita = math.ceil(
        (area_piso_m2 * 1.20 / RENDIMENTO_FITA_BRANCA_M2_POR_ROLO) * FATOR_SEGURANCA_FITA_BRANCA
    )
    item = await _buscar(db, "fita_branca")
    if not item:
        avisos.append("Nenhuma Fita Branca cadastrada no catálogo — item não incluído na lista.")
    elif rolos_fita > 0:
        itens.append(MaterialExtra(
            item="Fita Branca",
            qtd=f"{rolos_fita} rolo(s)",
            quantidade=float(rolos_fita),
            unidade="rolo",
            detalhe=f"{item.descricao} ({item.codigo_fabricante}) — {area_piso_m2:.2f}m² de piso",
            tipo_item="fita_branca",
        ))

    lona_m = (area_piso_m2 * 1.32) / 4.0
    item = await _buscar(db, "lona")
    if not item:
        avisos.append("Nenhuma Lona cadastrada no catálogo — item não incluído na lista.")
    else:
        itens.append(MaterialExtra(
            item="Lona",
            qtd=f"{lona_m:.2f} m",
            quantidade=round(lona_m, 2),
            unidade="m",
            detalhe=f"{item.descricao} ({item.codigo_fabricante}) — área do piso x 1,32 / 4",
            tipo_item="lona",
        ))

    return itens, avisos
