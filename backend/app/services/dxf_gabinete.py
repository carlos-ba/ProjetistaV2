"""Gera o projeto CAD da câmara em DXF via ezdxf (troca a versão anterior,
que escrevia DXF R12 em texto puro sem nenhuma cota real — só TEXT solto).

Unidade de trabalho = milímetros. Três vistas na mesma prancha, empilhadas
como no Visualizador Técnico da tela (Planta embaixo, Frontal e Lateral
acima, lado a lado):

  - Planta Baixa: contorno externo, área útil (recuada pela espessura do
    painel) e juntas de módulo nas 4 paredes;
  - Vista Frontal (comprimento x altura) e Vista Lateral (largura x altura):
    contorno + juntas de módulo na parede vista de frente, com a cota de
    altura (pé-direito) que não existia em nenhum lugar do DXF antigo;
  - Cotas em 3 níveis por eixo: geral (contorno externo), útil (área
    interna, só Planta) e cadeia de módulos (largura de cada painel) — mais
    a cota da espessura do painel. Cotas reais (entidade DIMENSION: linha de
    chamada, linha de extensão e seta), não texto solto como antes.
"""
from __future__ import annotations
import math
from io import StringIO

import ezdxf
from ezdxf.document import Drawing

from app.schemas.gabinete import GabineteDXFRequest

LAYER_CORES = {
    "CONTORNO":  7,   # branco/preto
    "AREA_UTIL": 4,   # ciano
    "PAINEIS":   5,   # azul
    "COTAS":     3,   # verde
    "TITULO":    2,   # amarelo
}

NIVEL_UTIL   = 1.6   # cota da área útil — mais perto do desenho
NIVEL_TOTAL  = 3.2   # cota do contorno externo
NIVEL_CADEIA = 4.8   # cadeia de módulos — nível mais externo


def _dim_override(h: float) -> dict:
    """Overrides de estilo de cota escalados pelo tamanho do desenho (mm) —
    o dimstyle padrão do ezdxf assume peças pequenas; sem isso, seta e texto
    saem microscópicos num desenho de metros."""
    return {
        "dimtxt": h,            # altura do texto
        "dimasz": h * 0.6,      # tamanho da seta
        "dimexe": h * 0.35,     # quanto a linha de extensão passa da linha de cota
        "dimexo": h * 0.2,      # afastamento da linha de extensão em relação ao objeto
        "dimtad": 1,            # texto acima da linha de cota
        "dimclrd": LAYER_CORES["COTAS"],
        "dimclre": LAYER_CORES["COTAS"],
        "dimclrt": LAYER_CORES["COTAS"],
        # O dimstyle padrão "EZDXF" do setup=True vem com dimlfac=100 (template
        # cm->mm) — sem zerar isso, todo texto de cota sai 100x maior que o
        # valor real (achado testando: "9700" virava "970000").
        "dimlfac": 1.0,
        "dimdec": 0,   # medidas em mm inteiro — sem casas decimais
    }


def _cota_h(msp, x: float, y_objeto: float, x1: float, x2: float, offset: float, h: float) -> None:
    """Cota linear horizontal — mede de x1 a x2, linha de cota deslocada
    `offset` (mm, negativo = abaixo) de y_objeto."""
    y = y_objeto + offset
    dim = msp.add_linear_dim(
        base=(x, y), p1=(x1, y_objeto), p2=(x2, y_objeto), angle=0,
        dimstyle="EZDXF", override=_dim_override(h),
        dxfattribs={"layer": "COTAS"},
    )
    dim.render()


def _cota_v(msp, y: float, x_objeto: float, y1: float, y2: float, offset: float, h: float) -> None:
    """Cota linear vertical — mede de y1 a y2, linha de cota deslocada
    `offset` (mm, negativo = à esquerda) de x_objeto."""
    x = x_objeto + offset
    dim = msp.add_linear_dim(
        base=(x, y), p1=(x_objeto, y1), p2=(x_objeto, y2), angle=90,
        dimstyle="EZDXF", override=_dim_override(h),
        dxfattribs={"layer": "COTAS"},
    )
    dim.render()


def _juntas_modulo(largura_total: float, modulo: float) -> list[float]:
    """Posições (a partir de 0) de cada junta de painel ao longo de um lado —
    o módulo final some da lista se ele já coincide com a borda (evita cota
    de largura ~0)."""
    n_inteiros = int(largura_total // modulo)
    posicoes = [i * modulo for i in range(1, n_inteiros + 1)]
    if posicoes and abs(posicoes[-1] - largura_total) < 0.5:
        posicoes.pop()
    return posicoes


def _cadeia_h(msp, oy: float, ox: float, largura: float, modulo: float, offset: float, h: float) -> None:
    juntas = [0.0] + _juntas_modulo(largura, modulo) + [largura]
    for a, b in zip(juntas, juntas[1:]):
        if b - a > 1:
            _cota_h(msp, ox + (a + b) / 2, oy, ox + a, ox + b, offset, h)


def _cadeia_v(msp, ox: float, oy: float, altura: float, modulo: float, offset: float, h: float) -> None:
    juntas = [0.0] + _juntas_modulo(altura, modulo) + [altura]
    for a, b in zip(juntas, juntas[1:]):
        if b - a > 1:
            _cota_v(msp, oy + (a + b) / 2, ox, oy + a, oy + b, offset, h)


def _desenhar_vista(
    msp, origin: tuple[float, float], largura: float, altura: float,
    modulo: float, esp: float | None, h: float, titulo: str,
    modulos_x: bool, modulos_y: bool,
) -> None:
    """Desenha um retângulo (planta ou elevação) com juntas de módulo e cotas.

    `esp`: só a Planta informa isso — desenha a área útil recuada e cota os
    dois eixos em 3 níveis (útil/total/cadeia). Nas elevações (`esp=None`)
    o eixo Y é a altura (pé-direito): 1 cota só, sem área útil nem cadeia
    (parede é uma peça inteiriça na vertical, não empilha módulo).
    `modulos_x`/`modulos_y`: se essa vista mostra juntas de painel naquele
    eixo (Planta: paredes/teto nos dois eixos; Frontal/Lateral: só no eixo
    horizontal — a parede vista de frente/lado).
    """
    ox, oy = origin

    msp.add_lwpolyline(
        [(ox, oy), (ox + largura, oy), (ox + largura, oy + altura), (ox, oy + altura)],
        close=True, dxfattribs={"layer": "CONTORNO"},
    )

    tem_area_util = esp is not None and largura > 2 * esp and altura > 2 * esp
    if tem_area_util:
        msp.add_lwpolyline(
            [
                (ox + esp, oy + esp), (ox + largura - esp, oy + esp),
                (ox + largura - esp, oy + altura - esp), (ox + esp, oy + altura - esp),
            ],
            close=True, dxfattribs={"layer": "AREA_UTIL"},
        )

    # Juntas de módulo (tick marks atravessando a espessura da parede na
    # Planta, ou o pé-direito inteiro nas elevações).
    faixa = esp if esp is not None else altura
    if modulos_x:
        for x in _juntas_modulo(largura, modulo):
            msp.add_line((ox + x, oy), (ox + x, oy + faixa), dxfattribs={"layer": "PAINEIS"})
            if esp is not None:
                msp.add_line((ox + x, oy + altura - faixa), (ox + x, oy + altura), dxfattribs={"layer": "PAINEIS"})
    if modulos_y and esp is not None:
        for y in _juntas_modulo(altura, modulo):
            msp.add_line((ox, oy + y), (ox + esp, oy + y), dxfattribs={"layer": "PAINEIS"})
            msp.add_line((ox + largura - esp, oy + y), (ox + largura, oy + y), dxfattribs={"layer": "PAINEIS"})

    # ── Cotas — eixo X (largura do parâmetro) ───────────────────────────
    if esp is not None and largura > 2 * esp:
        _cota_h(msp, ox + largura / 2, oy, ox + esp, ox + largura - esp, -h * NIVEL_UTIL, h)
    _cota_h(msp, ox + largura / 2, oy, ox, ox + largura, -h * NIVEL_TOTAL, h)
    if modulos_x:
        _cadeia_h(msp, oy, ox, largura, modulo, -h * NIVEL_CADEIA, h)

    # ── Cotas — eixo Y (altura do parâmetro: largura da câmara na Planta,
    # pé-direito nas elevações) ──────────────────────────────────────────
    if esp is not None:
        if altura > 2 * esp:
            _cota_v(msp, oy + altura / 2, ox, oy + esp, oy + altura - esp, -h * NIVEL_UTIL, h)
        _cota_v(msp, oy + altura / 2, ox, oy, oy + altura, -h * NIVEL_TOTAL, h)
        if modulos_y:
            _cadeia_v(msp, ox, oy, altura, modulo, -h * NIVEL_CADEIA, h)
    else:
        _cota_v(msp, oy + altura / 2, ox, oy, oy + altura, -h * NIVEL_UTIL, h)

    msp.add_text(titulo, height=h, dxfattribs={"layer": "TITULO"}).set_placement(
        (ox, oy + altura + h * 1.4)
    )


def gerar_dxf_gabinete(req: GabineteDXFRequest) -> str:
    L = req.comprimento * 1000.0
    W = req.largura * 1000.0
    A = req.altura * 1000.0
    esp = float(req.espessura)                       # já em mm
    painel = max(req.largura_painel * 1000.0, 1.0)    # evita divisão por zero
    h = max(min(L, W) / 30.0, 80.0)                   # altura de texto/cota legível
    gap = h * 10
    # Planta usa cadeia de módulos nos dois eixos (5 níveis de cota: útil e
    # total nos dois eixos + cadeia horizontal) — reserva mais espaço acima
    # dela antes de começar as elevações.
    reserva_planta = h * (NIVEL_CADEIA + 2)

    doc: Drawing = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$INSUNITS"] = ezdxf.units.MM
    for nome, cor in LAYER_CORES.items():
        doc.layers.add(nome, color=cor)
    msp = doc.modelspace()

    # Planta Baixa — na base da prancha
    origin_planta = (0.0, 0.0)
    _desenhar_vista(
        msp, origin_planta, L, W, painel, esp, h, "PLANTA BAIXA",
        modulos_x=True, modulos_y=True,
    )

    # Vista Frontal (comprimento x altura) — acima da planta
    y_frontal = W + reserva_planta
    origin_frontal = (0.0, y_frontal)
    _desenhar_vista(
        msp, origin_frontal, L, A, painel, None, h, "VISTA FRONTAL",
        modulos_x=True, modulos_y=False,
    )

    # Vista Lateral (largura x altura) — ao lado da frontal
    origin_lateral = (L + gap, y_frontal)
    _desenhar_vista(
        msp, origin_lateral, W, A, painel, None, h, "VISTA LATERAL",
        modulos_x=True, modulos_y=False,
    )

    # Cota da espessura do painel — entre contorno externo e área útil da Planta
    if esp > 0:
        _cota_h(msp, esp / 2, 0.0, 0.0, esp, -h * (NIVEL_CADEIA + 1.6), h)

    n_modulos_comp = math.ceil(L / painel)
    n_modulos_larg = math.ceil(W / painel)
    titulo = (
        f"Camara {req.comprimento:.2f} x {req.largura:.2f} x {req.altura:.2f} m  "
        f"| Painel {req.largura_painel:.2f} m / {esp:.0f} mm  "
        f"| Modulos: {n_modulos_comp} (comp.) x {n_modulos_larg} (larg.)"
    )
    msp.add_text(titulo, height=h * 1.3, dxfattribs={"layer": "TITULO"}).set_placement(
        (0.0, y_frontal + A + h * 8)
    )

    buffer = StringIO()
    doc.write(buffer)
    return buffer.getvalue()
