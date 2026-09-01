"""Desmembramento do kit de montagem (Card 1) — perfis metálicos, selante,
rebite e parafuso+bucha, no lugar da antiga linha única "Acessórios de
Montagem (Kit)". Ver DESIGN_KIT_MONTAGEM_2026-09-01.md pras fórmulas.

Fica em serviço à parte de calculos_gabinete.py (não em routes_gabinete.py
diretamente) porque depende do banco (catálogo perfil_metalico/selante/rebite/
parafuso_bucha) e calculos_gabinete.py é síncrono/sem DB de propósito.
"""
from __future__ import annotations
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.perfil_metalico import PerfilMetalico
from app.models.kit_montagem import SelanteMontagem, Rebite, ParafusoBucha
from app.schemas.gabinete import MaterialExtra, PerfilManualItem


async def _buscar_perfil(
    db: AsyncSession,
    tipo: str,
    medida_1: int,
    *,
    medida_2: int | None = None,
    medida_2_min: float | None = None,
    medida_3: int | None = None,
) -> tuple[PerfilMetalico | None, bool]:
    """Busca perfil por tipo + medida_1 (+ medida_3 fixa, opcional).

    Com `medida_2`: busca exata. Com `medida_2_min`: busca a menor medida_2
    disponível >= alvo (fallback "próximo tamanho acima" — nunca abaixo).
    Entre empates na mesma medida_2, prefere a barra de maior comprimento
    (menos barras a comprar). Retorna (perfil, match_exato).
    """
    stmt = select(PerfilMetalico).where(
        PerfilMetalico.tipo == tipo,
        PerfilMetalico.medida_1_mm == medida_1,
    )
    if medida_3 is not None:
        stmt = stmt.where(PerfilMetalico.medida_3_mm == medida_3)
    if medida_2 is not None:
        stmt = stmt.where(PerfilMetalico.medida_2_mm == medida_2).order_by(
            PerfilMetalico.comprimento_mm.desc()
        )
    else:
        stmt = stmt.where(PerfilMetalico.medida_2_mm >= medida_2_min).order_by(
            PerfilMetalico.medida_2_mm.asc(), PerfilMetalico.comprimento_mm.desc()
        )
    perfil = (await db.execute(stmt.limit(1))).scalars().first()
    if not perfil:
        return None, False
    exato = medida_2 is not None or perfil.medida_2_mm == medida_2_min
    return perfil, exato


async def calcular_kit_montagem(
    db: AsyncSession,
    *,
    comprimento: float,
    largura: float,
    comp_parede_m: float,
    espessura_painel_mm: float,
    area_total_paineis_m2: float,
    largura_aba_padrao_mm: int,
    rendimento_selante_m_por_embalagem: float,
    fator_seguranca_selante: float,
    perfis_manuais: list[PerfilManualItem],
) -> tuple[list[MaterialExtra], list[str]]:
    itens: list[MaterialExtra] = []
    avisos: list[str] = []
    perimetro_m = 2 * comprimento + 2 * largura
    aba = largura_aba_padrao_mm

    metros_perfis_totais = 0.0  # barras×comprimento, auto + manual — selante/rebite
    metros_perfil_u = 0.0       # só perfil U, auto + manual — parafuso+bucha

    # Ângulo Externo: perímetro do teto + 4 subidas (altura da parede + espessura do teto)
    subida_ext = comp_parede_m + (espessura_painel_mm / 1000.0)
    necessario_ext = perimetro_m + 4 * subida_ext
    alvo_aba2_ext = aba + espessura_painel_mm
    perfil, exato = await _buscar_perfil(db, "Ângulo Externo", aba, medida_2_min=alvo_aba2_ext)
    if not perfil:
        avisos.append(
            f"Nenhum Perfil Ângulo Externo com aba {aba}mm no catálogo — item não incluído na lista. "
            f"Cadastre o perfil ou adicione manualmente."
        )
    if perfil:
        compr_m = perfil.comprimento_mm / 1000.0
        barras = math.ceil(necessario_ext / compr_m)
        metros_perfis_totais += barras * compr_m
        aviso = "" if exato else f" — sem medida exata (aba2 ideal {alvo_aba2_ext:.0f}mm), usado {perfil.medida_2_mm}mm"
        itens.append(MaterialExtra(
            item="Perfil Ângulo Externo",
            qtd=f"{barras} barra(s)",
            quantidade=float(barras),
            unidade="barra",
            detalhe=(
                f"{aba}x{perfil.medida_2_mm}x{perfil.comprimento_mm}mm — "
                f"{necessario_ext:.2f}m necessários ({perfil.codigo_fabricante}){aviso}"
            ),
            tipo_item="perfil_angulo_externo",
        ))

    # Ângulo Interno: perímetro do teto + 4 subidas (só altura da parede, sem espessura do teto)
    necessario_int = perimetro_m + 4 * comp_parede_m
    perfil, _ = await _buscar_perfil(db, "Ângulo Interno", aba, medida_2=aba)
    if not perfil:
        avisos.append(
            f"Nenhum Perfil Ângulo Interno {aba}x{aba}mm no catálogo — item não incluído na lista. "
            f"Cadastre o perfil ou adicione manualmente."
        )
    if perfil:
        compr_m = perfil.comprimento_mm / 1000.0
        barras = math.ceil(necessario_int / compr_m)
        metros_perfis_totais += barras * compr_m
        itens.append(MaterialExtra(
            item="Perfil Ângulo Interno",
            qtd=f"{barras} barra(s)",
            quantidade=float(barras),
            unidade="barra",
            detalhe=(
                f"{aba}x{aba}x{perfil.comprimento_mm}mm — "
                f"{necessario_int:.2f}m necessários ({perfil.codigo_fabricante})"
            ),
            tipo_item="perfil_angulo_interno",
        ))

    # U: perímetro do piso, sem subidas
    necessario_u = perimetro_m
    alvo_alma_u = espessura_painel_mm
    perfil, exato = await _buscar_perfil(db, "U", aba, medida_2_min=alvo_alma_u, medida_3=aba)
    if not perfil:
        avisos.append(
            f"Nenhum Perfil U com aba {aba}mm e alma ≥ {alvo_alma_u:.0f}mm no catálogo — item não incluído na lista. "
            f"Cadastre o perfil ou adicione manualmente."
        )
    if perfil:
        compr_m = perfil.comprimento_mm / 1000.0
        barras = math.ceil(necessario_u / compr_m)
        metros_perfis_totais += barras * compr_m
        metros_perfil_u += barras * compr_m
        aviso = "" if exato else f" — sem medida exata (alma ideal {alvo_alma_u:.0f}mm), usado {perfil.medida_2_mm}mm"
        itens.append(MaterialExtra(
            item="Perfil U",
            qtd=f"{barras} barra(s)",
            quantidade=float(barras),
            unidade="barra",
            detalhe=(
                f"{aba}x{perfil.medida_2_mm}x{aba}x{perfil.comprimento_mm}mm — "
                f"{necessario_u:.2f}m necessários ({perfil.codigo_fabricante}){aviso}"
            ),
            tipo_item="perfil_u",
        ))

    # Perfis extras (seleção manual — Liso, Z, variações fora do padrão)
    for manual in perfis_manuais:
        perfil = await db.get(PerfilMetalico, manual.perfil_id)
        if not perfil:
            continue
        compr_m = perfil.comprimento_mm / 1000.0
        metros_perfis_totais += manual.quantidade_barras * compr_m
        if perfil.tipo == "U":
            metros_perfil_u += manual.quantidade_barras * compr_m
        itens.append(MaterialExtra(
            item=f"Perfil {perfil.tipo} (manual)",
            qtd=f"{manual.quantidade_barras} barra(s)",
            quantidade=float(manual.quantidade_barras),
            unidade="barra",
            detalhe=f"{perfil.descricao_original} ({perfil.codigo_fabricante}) — seleção manual",
            tipo_item="perfil_manual",
        ))

    # Selante de PU: (perfis×2 + painéis×0,145) ÷ rendimento, com fator de segurança
    rendimento = rendimento_selante_m_por_embalagem or 12.0
    consumo_perfis_emb = (metros_perfis_totais * 2) / rendimento
    consumo_paineis_emb = (area_total_paineis_m2 * 0.145) / rendimento
    embalagens_selante = math.ceil((consumo_perfis_emb + consumo_paineis_emb) * (1 + fator_seguranca_selante))
    selante = (await db.execute(select(SelanteMontagem).order_by(SelanteMontagem.id).limit(1))).scalars().first()
    if not selante and embalagens_selante > 0:
        avisos.append("Nenhum Selante de PU cadastrado no catálogo — item não incluído na lista.")
    if selante and embalagens_selante > 0:
        itens.append(MaterialExtra(
            item="Selante de PU",
            qtd=f"{embalagens_selante} embalagem(ns)",
            quantidade=float(embalagens_selante),
            unidade="embalagem",
            detalhe=(
                f"{selante.descricao} ({selante.codigo_fabricante}) — "
                f"{metros_perfis_totais:.1f}m de perfil + {area_total_paineis_m2:.1f}m² de painel"
            ),
            tipo_item="selante_montagem",
        ))

    # Rebite: 2 linhas a cada 200mm em todos os perfis
    rebites = math.ceil(metros_perfis_totais * 1000 / 200) * 2
    rebite = (await db.execute(select(Rebite).order_by(Rebite.id).limit(1))).scalars().first()
    if not rebite and rebites > 0:
        avisos.append("Nenhum Rebite cadastrado no catálogo — item não incluído na lista.")
    if rebite and rebites > 0:
        itens.append(MaterialExtra(
            item="Rebite",
            qtd=f"{rebites} un.",
            quantidade=float(rebites),
            unidade="un",
            detalhe=f"{rebite.descricao} ({rebite.codigo_fabricante}) — 2 linhas a cada 200mm, {metros_perfis_totais:.1f}m de perfil",
            tipo_item="rebite",
        ))

    # Parafuso + Bucha: 1 linha a cada 500mm, só no perfil U (piso)
    parafusos = math.ceil(metros_perfil_u * 1000 / 500)
    parafuso = (await db.execute(select(ParafusoBucha).order_by(ParafusoBucha.id).limit(1))).scalars().first()
    if not parafuso and parafusos > 0:
        avisos.append("Nenhum Conjunto Parafuso + Bucha cadastrado no catálogo — item não incluído na lista.")
    if parafuso and parafusos > 0:
        itens.append(MaterialExtra(
            item="Conjunto Parafuso + Bucha",
            qtd=f"{parafusos} un.",
            quantidade=float(parafusos),
            unidade="un",
            detalhe=f"{parafuso.descricao} ({parafuso.codigo_fabricante}) — 1 linha a cada 500mm no perfil U, {metros_perfil_u:.1f}m",
            tipo_item="parafuso_bucha",
        ))

    return itens, avisos
