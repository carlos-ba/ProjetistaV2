"""Kit de montagem (Card 1) — regras de 2026-10-20:

  * Perfil U do piso só existe quando o piso NÃO é em painel (convencional, apoiado ou rebaixado,
    ou sem piso). Com piso em painel o acabamento parede × painel de piso é o Ângulo Externo
    sobreposto: soma uma volta extra (perímetro do piso) no Ângulo Externo e não gera U — nem
    Parafuso + Bucha (que só acompanha o U do piso).
  * Perfil T entra nos metros de selante e rebite (metros reais: barras × comprimento), como os
    demais perfis; Parafuso + Bucha continua só do U.

Roda contra o catálogo real do banco local de desenvolvimento (perfis MBP Isoblock, Perfil T,
selante/rebite/parafuso), mesma estratégia da suíte do webhook. Câmara de referência 5×4×3 m,
painel de 70 mm, largura de painel 1,15 m, aba padrão 40 mm.
"""
import math

import pytest

from app.services.kit_montagem import _buscar_perfil, calcular_kit_montagem

COMP, LARG, ESP_MM = 5.0, 4.0, 70.0
PERIMETRO = 2 * COMP + 2 * LARG          # 18 m
AREA_PAINEIS = 98.62                     # m² (paredes + teto + piso, câmara de referência)
FATOR, REND = 0.10, 12.0


def comp_parede(tipo_piso: str) -> float:
    return round(3.0 - (2 if tipo_piso == "painel" else 1) * ESP_MM / 1000.0, 3)


async def _kit(db, tipo_piso, linhas_t=0, comprimento=COMP):
    itens, avisos = await calcular_kit_montagem(
        db,
        comprimento=comprimento, largura=LARG,
        comp_parede_m=comp_parede(tipo_piso), espessura_painel_mm=ESP_MM,
        area_total_paineis_m2=AREA_PAINEIS,
        largura_aba_padrao_mm=40, rendimento_selante_m_por_embalagem=REND,
        fator_seguranca_selante=FATOR, perfis_manuais=[],
        largura_painel=1.15, linhas_sustentacao_perfil_t=linhas_t,
        tipo_piso=tipo_piso,
    )
    return {i.tipo_item: i for i in itens}, avisos


async def _compr(db, tipo, medida_1, **kw) -> float:
    perfil, _ = await _buscar_perfil(db, tipo, medida_1, **kw)
    assert perfil, f"catálogo local sem {tipo} {medida_1}"
    return perfil.comprimento_mm / 1000.0


@pytest.mark.asyncio
async def test_kit_1_piso_painel_nao_gera_u_nem_parafuso_e_soma_volta_no_angulo_externo(db):
    itens, _ = await _kit(db, "painel")
    assert "perfil_u" not in itens
    assert "parafuso_bucha" not in itens
    L = await _compr(db, "Ângulo Externo", 40, medida_2_min=40 + ESP_MM)
    subida = comp_parede("painel") + ESP_MM / 1000.0
    esperado = math.ceil((PERIMETRO + 4 * subida + PERIMETRO) / L)   # teto + subidas + volta do piso
    assert itens["perfil_angulo_externo"].quantidade == esperado
    assert "volta do piso em painel" in itens["perfil_angulo_externo"].detalhe


@pytest.mark.asyncio
@pytest.mark.parametrize("tipo_piso", ["convencional", "nenhum"])
async def test_kit_2_piso_convencional_ou_sem_piso_gera_u_e_parafuso_sem_volta_extra(db, tipo_piso):
    itens, _ = await _kit(db, tipo_piso)
    assert "perfil_u" in itens and "parafuso_bucha" in itens
    Lu = await _compr(db, "U", 40, medida_2_min=ESP_MM, medida_3=40)
    assert itens["perfil_u"].quantidade == math.ceil(PERIMETRO / Lu)
    L = await _compr(db, "Ângulo Externo", 40, medida_2_min=40 + ESP_MM)
    subida = comp_parede(tipo_piso) + ESP_MM / 1000.0
    assert itens["perfil_angulo_externo"].quantidade == math.ceil((PERIMETRO + 4 * subida) / L)
    assert "volta do piso" not in itens["perfil_angulo_externo"].detalhe
    metros_u = itens["perfil_u"].quantidade * Lu
    assert itens["parafuso_bucha"].quantidade == math.ceil(metros_u * 1000 / 500)


@pytest.mark.asyncio
async def test_kit_3_perfil_t_entra_em_selante_e_rebite_mas_nao_em_parafuso(db):
    # câmara comprida e estreita o bastante pra 1 linha de Perfil T: 10 m de comprimento, 1 linha
    base, _ = await _kit(db, "convencional", linhas_t=0, comprimento=10.0)
    com_t, avisos = await _kit(db, "convencional", linhas_t=1, comprimento=10.0)
    if "perfil_t" not in com_t:
        pytest.skip("catálogo local sem Perfil T")
    assert "perfil_t" not in base

    barras_t = com_t["perfil_t"].quantidade
    # metros reais do T = barras × comprimento da barra (a maior cadastrada) — lido do catálogo
    from sqlalchemy import select
    from app.models.perfil_metalico import PerfilMetalico
    perfil_t = (await db.execute(
        select(PerfilMetalico).where(PerfilMetalico.tipo == "T").order_by(PerfilMetalico.comprimento_mm.desc()).limit(1)
    )).scalars().first()
    metros_t = barras_t * perfil_t.comprimento_mm / 1000.0
    assert barras_t == math.ceil(10.0 / (perfil_t.comprimento_mm / 1000.0))

    # metros dos demais perfis: mesma câmara, sem o T (recompõe pelos itens e comprimentos do catálogo)
    Lext = await _compr(db, "Ângulo Externo", 40, medida_2_min=40 + ESP_MM)
    Lint = await _compr(db, "Ângulo Interno", 40, medida_2=40)
    Lu = await _compr(db, "U", 40, medida_2_min=ESP_MM, medida_3=40)
    m_base = (base["perfil_angulo_externo"].quantidade * Lext
              + base["perfil_angulo_interno"].quantidade * Lint
              + base["perfil_u"].quantidade * Lu)

    assert com_t["rebite"].quantidade == math.ceil((m_base + metros_t) * 1000 / 200) * 2
    assert base["rebite"].quantidade == math.ceil(m_base * 1000 / 200) * 2
    esperado_selante = math.ceil(((m_base + metros_t) * 2 / REND + AREA_PAINEIS * 0.145 / REND) * (1 + FATOR))
    assert com_t["selante_montagem"].quantidade == esperado_selante
    assert com_t["selante_montagem"].quantidade > base["selante_montagem"].quantidade
    # parafuso+bucha segue só o U: igual com e sem T
    assert com_t["parafuso_bucha"].quantidade == base["parafuso_bucha"].quantidade


@pytest.mark.asyncio
async def test_kit_4_piso_painel_total_de_perfis_considera_so_externo_e_interno(db):
    itens, _ = await _kit(db, "painel")
    Lext = await _compr(db, "Ângulo Externo", 40, medida_2_min=40 + ESP_MM)
    Lint = await _compr(db, "Ângulo Interno", 40, medida_2=40)
    metros = itens["perfil_angulo_externo"].quantidade * Lext + itens["perfil_angulo_interno"].quantidade * Lint
    assert itens["rebite"].quantidade == math.ceil(metros * 1000 / 200) * 2
    esperado = math.ceil((metros * 2 / REND + AREA_PAINEIS * 0.145 / REND) * (1 + FATOR))
    assert itens["selante_montagem"].quantidade == esperado
