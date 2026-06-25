"""
Seleção de válvula solenoide Danfoss EVR por cálculo de Kv.

Fórmula:  Q [kW] = Kv × √(1000 × ΔP × ρ_L) × Δh / 3600
Onde:
  Kv   = coeficiente de vazão [m³/h]
  ΔP   = queda de pressão na válvula [bar]  (padrão 0,10 bar linha líquido)
  ρ_L  = densidade do líquido na T.condensação [kg/m³]
  Δh   = h_vapor(te) − h_liquido(tc) [kJ/kg]

Fonte das propriedades: CoolPack / DuPont SUVA HP62 (R404A), ASHRAE 1974 (R22)
"""

import math
from typing import Optional

# ── Tabelas termodinâmicas de saturação ─────────────────────────────────────
# Fonte: CoolPack (DTU), exportado 2026-06-25
# Colunas: T(°C), P_sat(bar), Vl(dm³/kg), Hl(kJ/kg), Hg(kJ/kg)

_R404A = [
    (-45, 1.055, 0.7816, 138.57, 340.57),
    (-40, 1.330, 0.7911, 144.83, 343.81),
    (-35, 1.658, 0.8012, 151.65, 347.05),
    (-30, 2.045, 0.8121, 159.17, 350.26),
    (-25, 2.499, 0.8236, 165.57, 353.41),
    (-20, 3.027, 0.8361, 172.08, 356.52),
    (-15, 3.635, 0.8495, 178.71, 359.58),
    (-10, 4.333, 0.8640, 185.48, 362.56),
    ( -5, 5.128, 0.8798, 192.37, 365.47),
    (  0, 6.028, 0.8970, 199.41, 368.28),
    (  5, 7.043, 0.9158, 206.60, 370.99),
    ( 10, 8.180, 0.9366, 213.96, 373.58),
    ( 15, 9.451, 0.9596, 221.52, 376.02),
    ( 20,10.864, 0.9852, 229.29, 378.29),
    ( 25,12.430, 1.0141, 237.31, 380.37),
    ( 30,14.160, 1.0469, 245.60, 382.21),
    ( 35,16.065, 1.0845, 254.21, 383.78),
    ( 40,18.157, 1.1284, 263.20, 385.01),
    ( 45,20.449, 1.1806, 272.66, 385.82),
    ( 50,22.953, 1.2439, 282.69, 386.08),
    ( 55,25.685, 1.3236, 293.51, 385.60),
]

_R22 = [
    (-45, 0.827, 0.7022, 150.14, 386.29),
    (-40, 1.049, 0.7093, 155.40, 388.62),
    (-35, 1.317, 0.7168, 160.73, 390.91),
    (-30, 1.635, 0.7245, 166.13, 393.15),
    (-25, 2.010, 0.7325, 171.60, 395.34),
    (-20, 2.448, 0.7409, 177.13, 397.48),
    (-15, 2.957, 0.7496, 182.74, 399.55),
    (-10, 3.543, 0.7587, 188.42, 401.56),
    ( -5, 4.213, 0.7683, 194.17, 403.51),
    (  0, 4.976, 0.7783, 200.00, 405.37),
    (  5, 5.838, 0.7889, 205.90, 407.15),
    ( 10, 6.807, 0.8000, 211.88, 408.84),
    ( 15, 7.891, 0.8118, 217.92, 410.44),
    ( 20, 9.099, 0.8243, 224.07, 411.93),
    ( 25,10.439, 0.8376, 230.31, 413.30),
    ( 30,11.919, 0.8519, 236.65, 414.54),
    ( 35,13.548, 0.8673, 243.10, 415.64),
    ( 40,15.335, 0.8839, 249.67, 416.57),
    ( 45,17.290, 0.9020, 256.38, 417.32),
    ( 50,19.423, 0.9219, 263.25, 417.85),
    ( 55,21.744, 0.9440, 270.31, 418.13),
]

_TABELAS = {
    "R404A": _R404A,
    "R404A/R507": _R404A,
    "R22": _R22,
}

# ── Tabela EVR v2 — Kv (m³/h) ───────────────────────────────────────────────
# Fonte: Danfoss Coolselector2 v5.6.13, testado 2026-06-25
# Ordem crescente de Kv (= ordem crescente de capacidade)
EVR_MODELOS = [
    {"modelo": "EVR 2 v2",     "kv": 0.15, "ns": 6},
    {"modelo": "EVR 3 v2",     "kv": 0.26, "ns": 6},
    {"modelo": "EVR 4 v2",     "kv": 0.70, "ns": 10},
    {"modelo": "EVR 6 man v2", "kv": 0.80, "ns": 10},
    {"modelo": "EVR 6 v2",     "kv": 1.00, "ns": 10},
    {"modelo": "EVR 8 v2",     "kv": 1.40, "ns": 10},
    {"modelo": "EVR 10 v2",    "kv": 2.00, "ns": 10},
    {"modelo": "EVR 15 v2",    "kv": 3.20, "ns": 10},
    {"modelo": "EVR 18 v2",    "kv": 4.30, "ns": 10},
    {"modelo": "EVR 20 v2",    "kv": 6.50, "ns": 10},
    {"modelo": "EVR 22 v2",    "kv": 7.80, "ns": 10},
    {"modelo": "EVR 25 v2",    "kv": 8.50, "ns": 10},
    {"modelo": "EVR 32 v2",    "kv":14.00, "ns": 10},
    {"modelo": "EVR 40 v2",    "kv":20.00, "ns": 10},
]


def _interpolar(tabela: list, t: float, col: int) -> float:
    """Interpolação linear entre os pontos da tabela."""
    temps = [row[0] for row in tabela]
    vals  = [row[col] for row in tabela]

    if t <= temps[0]:
        return vals[0]
    if t >= temps[-1]:
        return vals[-1]

    for i in range(len(temps) - 1):
        if temps[i] <= t <= temps[i + 1]:
            frac = (t - temps[i]) / (temps[i + 1] - temps[i])
            return vals[i] + frac * (vals[i + 1] - vals[i])
    return vals[-1]


def propriedades(fluido: str, t: float) -> dict:
    """Retorna propriedades termodinâmicas interpoladas para o fluido na temperatura t (°C)."""
    fluido_key = fluido.upper().replace(" ", "")
    tabela = None
    for k, v in _TABELAS.items():
        if k.upper().replace(" ", "") == fluido_key:
            tabela = v
            break
    if tabela is None:
        raise ValueError(f"Fluido '{fluido}' não suportado. Use R404A ou R22.")

    vl  = _interpolar(tabela, t, 2)   # dm³/kg
    hl  = _interpolar(tabela, t, 3)   # kJ/kg
    hg  = _interpolar(tabela, t, 4)   # kJ/kg
    rho = 1000.0 / vl                  # kg/m³

    return {"t": t, "vl": vl, "rho_L": rho, "h_L": hl, "h_V": hg}


def calcular_capacidade(kv: float, rho_L: float, delta_h: float, dp_bar: float = 0.10) -> float:
    """Capacidade em kW para uma válvula com Kv dado."""
    return kv * math.sqrt(1000.0 * dp_bar * rho_L) * delta_h / 3600.0


def selecionar_solenoide(
    fluido: str,
    te: float,
    tc: float,
    capacidade_kw: float,
    dp_bar: float = 0.10,
    margem: float = 1.10,
) -> dict:
    """
    Seleciona a menor válvula EVR v2 que atende a capacidade requerida.

    Args:
        fluido:         'R404A' ou 'R22'
        te:             temperatura de evaporação (°C)
        tc:             temperatura de condensação (°C)
        capacidade_kw:  carga térmica na linha de líquido (kW)
        dp_bar:         queda de pressão admissível (bar), padrão 0,10
        margem:         fator de segurança (padrão 10%)

    Returns:
        dict com modelo selecionado, capacidade calculada, Kv e propriedades.
    """
    fluido_norm = fluido.upper().replace(" ", "")
    tabela = None
    for k, v in _TABELAS.items():
        if k.upper().replace(" ", "") == fluido_norm:
            tabela = v
            break
    if tabela is None:
        raise ValueError(f"Fluido '{fluido}' não suportado.")

    prop_e = propriedades(fluido, te)
    prop_c = propriedades(fluido, tc)

    h_V   = prop_e["h_V"]
    h_L   = prop_c["h_L"]
    rho_L = prop_c["rho_L"]
    delta_h = h_V - h_L

    cap_minima = capacidade_kw * margem

    candidatos = []
    for evr in EVR_MODELOS:
        kv = evr["kv"]
        q  = calcular_capacidade(kv, rho_L, delta_h, dp_bar)
        candidatos.append({
            "modelo":        evr["modelo"],
            "kv":            kv,
            "capacidade_kw": round(q, 2),
            "adequado":      q >= cap_minima,
        })

    selecionado = next((c for c in candidatos if c["adequado"]), candidatos[-1])

    return {
        "fluido":           fluido,
        "te_c":             te,
        "tc_c":             tc,
        "capacidade_kw":    round(capacidade_kw, 2),
        "dp_bar":           dp_bar,
        "rho_L_kg_m3":      round(rho_L, 1),
        "delta_h_kj_kg":    round(delta_h, 2),
        "modelo":           selecionado["modelo"],
        "kv":               selecionado["kv"],
        "capacidade_valvula_kw": selecionado["capacidade_kw"],
        "fator_servico":    round(selecionado["capacidade_kw"] / capacidade_kw, 2),
        "candidatos":       candidatos,
    }
