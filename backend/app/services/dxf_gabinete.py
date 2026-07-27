"""Gera a planta baixa da câmara em DXF (AutoCAD R12) sem dependências externas.

O DXF é um formato texto: emitimos apenas as seções mínimas (HEADER + ENTITIES)
com entidades LINE e TEXT. Unidade de trabalho = milímetros.

Vista em planta (olhando de cima):
  - retângulo externo (comprimento x largura);
  - retângulo interno (recuado pela espessura do painel) = área útil;
  - juntas dos painéis de teto (linhas a cada largura_painel ao longo do comprimento);
  - cotas de texto com as dimensões.
"""
from __future__ import annotations
import math

from app.schemas.gabinete import GabineteDXFRequest


def _line(x1: float, y1: float, x2: float, y2: float, layer: str) -> str:
    return (
        f"0\nLINE\n8\n{layer}\n"
        f"10\n{x1:.3f}\n20\n{y1:.3f}\n30\n0.0\n"
        f"11\n{x2:.3f}\n21\n{y2:.3f}\n31\n0.0\n"
    )


def _text(x: float, y: float, h: float, s: str, layer: str) -> str:
    return f"0\nTEXT\n8\n{layer}\n10\n{x:.3f}\n20\n{y:.3f}\n30\n0.0\n40\n{h:.3f}\n1\n{s}\n"


def gerar_dxf_gabinete(req: GabineteDXFRequest) -> str:
    # metros -> mm
    L = req.comprimento * 1000.0
    W = req.largura * 1000.0
    esp = float(req.espessura)                       # já em mm
    painel = max(req.largura_painel * 1000.0, 1.0)   # evita divisão por zero
    h = max(min(L, W) / 30.0, 80.0)                  # altura de texto legível

    ents: list[str] = []

    # Retângulo externo
    ents += [
        _line(0, 0, L, 0, "CONTORNO"),
        _line(L, 0, L, W, "CONTORNO"),
        _line(L, W, 0, W, "CONTORNO"),
        _line(0, W, 0, 0, "CONTORNO"),
    ]

    # Retângulo interno (área útil) — só se couber
    if L > 2 * esp and W > 2 * esp:
        ents += [
            _line(esp, esp, L - esp, esp, "AREA_UTIL"),
            _line(L - esp, esp, L - esp, W - esp, "AREA_UTIL"),
            _line(L - esp, W - esp, esp, W - esp, "AREA_UTIL"),
            _line(esp, W - esp, esp, esp, "AREA_UTIL"),
        ]

    # Juntas dos painéis de teto (ao longo do comprimento)
    n_paineis = math.ceil(L / painel)
    x = painel
    while x < L - 0.5:
        ents.append(_line(x, 0, x, W, "PAINEIS"))
        x += painel

    # Cotas / rótulos
    ents += [
        _text(L / 2 - (len("Comprimento") * h * 0.35), -h * 2.2,
              h, f"Comprimento: {req.comprimento:.2f} m", "COTAS"),
        _text(-h * 0.6, W / 2, h, f"Largura: {req.largura:.2f} m", "COTAS"),
        _text(0, W + h * 1.2, h,
              f"Camara {req.comprimento:.2f} x {req.largura:.2f} x {req.altura:.2f} m  "
              f"| Painel {req.largura_painel:.2f} m / {esp:.0f} mm  "
              f"| Teto: {n_paineis} paineis", "TITULO"),
    ]

    corpo = "".join(ents)
    return (
        "0\nSECTION\n2\nHEADER\n"
        "9\n$INSUNITS\n70\n4\n"           # 4 = milímetros
        "9\n$ACADVER\n1\nAC1009\n"        # R12
        "0\nENDSEC\n"
        "0\nSECTION\n2\nENTITIES\n"
        f"{corpo}"
        "0\nENDSEC\n"
        "0\nEOF\n"
    )
