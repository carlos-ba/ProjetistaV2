"""
Estimativa de carga de fluido refrigerante (kg).

Fórmula:
    Carga total = volume_evaporador (kg, do catálogo)
                + volume_linha_líquido (L) × ρ_líquido (kg/L)
                + volume_linha_sucção  (L) × ρ_vapor   (kg/L)

Volumes das linhas calculados a partir dos diâmetros internos e comprimentos.
Densidades: valores médios de catálogo ASHRAE / Danfoss, saturado na T.Evap típica.

Referência bitola → diâmetro interno Cu (mm):
  Norma ASTM B280 / EN 12735 — tubo de cobre para refrigeração.
"""

import math

# ── Diâmetro INTERNO do tubo de cobre (mm) por bitola ──────────────────────
# Bitola = OD nominal. Espessura de parede: 0,89 mm (até 7/8") / 1,02 mm (acima)
_DI_MM: dict[str, float] = {
    '3/8"':   7.92,
    '1/2"':  10.92,
    '5/8"':  13.84,
    '3/4"':  17.07,
    '7/8"':  20.22,
    '1.1/8"': 26.04,
    '1.3/8"': 32.51,
    '1.5/8"': 38.96,
    '2.1/8"': 52.38,
}

# ── Densidades médias (kg/L) — líquido saturado e vapor saturado ────────────
# Fonte: tabelas ASHRAE 2017 Fundamentals, Cap. 30
# Valores para T.Evap = -10°C (câmara fria típica de -18°C → T.Evap ~-25°C usa R22)
# Conservador: usar densidade de líquido a ~25°C (temperatura da linha de líquido)
_RHO_LIQUIDO: dict[str, float] = {   # kg/L de líquido saturado a ~25°C
    'R22':   1.149,
    'R404A': 1.048,
    'R448A': 1.055,
    'R449A': 1.052,
    'R407C': 1.117,
    'R134A': 1.207,
}

_RHO_VAPOR: dict[str, float] = {     # kg/L de vapor saturado a T.Evap ~ -10°C
    'R22':   0.0239,
    'R404A': 0.0386,
    'R448A': 0.0375,
    'R449A': 0.0368,
    'R407C': 0.0258,
    'R134A': 0.0145,
}

_FLUIDO_FALLBACK = 'R22'


def _volume_tubo_litros(bitola: str, comprimento_m: float) -> float:
    """Volume interno de um tubo de cobre em litros."""
    di = _DI_MM.get(bitola)
    if di is None or comprimento_m <= 0:
        return 0.0
    raio_m = (di / 1000) / 2
    return math.pi * raio_m ** 2 * comprimento_m * 1000  # m³ → litros


def estimar_carga_fluido(
    fluido: str,
    volume_interno_evap_kg: float | None,
    bitola_liquido: str,
    comprimento_liquido_m: float,
    bitola_succao: str,
    comprimento_succao_m: float,
) -> dict:
    """
    Estima a carga total de fluido refrigerante do sistema.

    Args:
        fluido:                 R404A, R22, etc.
        volume_interno_evap_kg: volume interno do evaporador em kg (do catálogo)
        bitola_liquido:         ex: '1/2"'
        comprimento_liquido_m:  comprimento da linha de líquido em metros
        bitola_succao:          ex: '7/8"'
        comprimento_succao_m:   comprimento da linha de sucção em metros

    Returns:
        dict com carga por componente e total em kg
    """
    fluido_key = fluido.upper().replace('-', '')
    rho_liq  = _RHO_LIQUIDO.get(fluido_key,  _RHO_LIQUIDO[_FLUIDO_FALLBACK])
    rho_vap  = _RHO_VAPOR.get(fluido_key,    _RHO_VAPOR[_FLUIDO_FALLBACK])

    vol_liq_L  = _volume_tubo_litros(bitola_liquido, comprimento_liquido_m)
    vol_suc_L  = _volume_tubo_litros(bitola_succao,  comprimento_succao_m)

    carga_liq  = round(vol_liq_L * rho_liq, 3)
    carga_suc  = round(vol_suc_L * rho_vap, 3)
    carga_evap = round(float(volume_interno_evap_kg), 3) if volume_interno_evap_kg else 0.0
    carga_total = round(carga_evap + carga_liq + carga_suc, 2)

    nota = ""
    if fluido_key not in _RHO_LIQUIDO:
        nota = f"Fluido {fluido} sem tabela própria — usando R22 como referência"

    return {
        "fluido":              fluido,
        "carga_evaporador_kg": carga_evap,
        "carga_linha_liquido_kg": carga_liq,
        "carga_linha_succao_kg":  carga_suc,
        "carga_total_kg":      carga_total,
        "detalhes": {
            "vol_liquido_L":  round(vol_liq_L, 3),
            "vol_succao_L":   round(vol_suc_L, 3),
            "rho_liquido":    rho_liq,
            "rho_vapor":      rho_vap,
            "bitola_liquido": bitola_liquido,
            "bitola_succao":  bitola_succao,
        },
        "nota": nota,
    }
