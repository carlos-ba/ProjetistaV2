"""
Seleção automática de tanque de líquido vertical.

Critério: ABNT NBR 16.069 — máximo recolhimento considera 80% do volume TOTAL.
O tanque selecionado deve satisfazer:
    volume_total × 0,80 ≥ carga_total_kg / ρ_líquido

Fontes:
  RAC Brasil — série VLR (catálogo 2025)
  Castel — série 6580 (catálogo técnico)
"""

# ── Densidades do líquido saturado a ~25°C (kg/L) ────────────────────────
# Usadas para converter carga em kg → volume necessário em litros
_RHO_LIQUIDO: dict[str, float] = {
    'R22':   1.149,
    'R404A': 1.048,
    'R448A': 1.055,
    'R449A': 1.052,
    'R407C': 1.117,
    'R134A': 1.207,
    'R410A': 1.059,
    'R32':   0.961,
    'R290':  0.501,
}
_RHO_FALLBACK = 1.048  # R404A como referência conservadora

# ── Tabela de tanques ─────────────────────────────────────────────────────
# volume_util_l = volume_total_l × 0,80  (NBR 16.069)
_TANQUES: list[dict] = [
    # Castel série 6580 — para sistemas pequenos
    {"fabricante": "Castel", "modelo": "6580/2",  "volume_total_l":  2.1, "conexao": '3/8"'},
    {"fabricante": "Castel", "modelo": "6580/3",  "volume_total_l":  3.6, "conexao": '1/2"'},
    {"fabricante": "Castel", "modelo": "6580/4",  "volume_total_l":  5.4, "conexao": '5/8"'},
    {"fabricante": "Castel", "modelo": "6580/5",  "volume_total_l":  7.3, "conexao": '3/4"'},
    {"fabricante": "Castel", "modelo": "6580/6",  "volume_total_l": 10.8, "conexao": '7/8"'},
    {"fabricante": "Castel", "modelo": "6580/8",  "volume_total_l": 19.6, "conexao": '1.1/8"'},
    {"fabricante": "Castel", "modelo": "6580/10", "volume_total_l": 26.9, "conexao": '1.3/8"'},
    # RAC Brasil série VLR — para sistemas médios e grandes
    {"fabricante": "RAC",   "modelo": "VLR-30",  "volume_total_l":  35.0, "conexao": '7/8"'},
    {"fabricante": "RAC",   "modelo": "VLR-50",  "volume_total_l":  59.0, "conexao": '1.3/8"'},
    {"fabricante": "RAC",   "modelo": "VLR-75",  "volume_total_l":  79.0, "conexao": '1.3/8"'},
    {"fabricante": "RAC",   "modelo": "VLR-100", "volume_total_l": 130.0, "conexao": '1.5/8"'},
    {"fabricante": "RAC",   "modelo": "VLR-150", "volume_total_l": 166.0, "conexao": '2.1/8"'},
    {"fabricante": "RAC",   "modelo": "VLR-200", "volume_total_l": 223.0, "conexao": '2.1/8"'},
]

# Pré-calcula volume útil (80%) em cada modelo
for _t in _TANQUES:
    _t["volume_util_l"] = round(_t["volume_total_l"] * 0.80, 1)


def selecionar_tanque_liquido(
    fluido: str,
    carga_total_kg: float,
) -> dict:
    """
    Seleciona o menor tanque de líquido que atende à NBR 16.069.

    Args:
        fluido:         R404A, R22, etc.
        carga_total_kg: carga total de fluido do sistema em kg

    Returns:
        dict com tanque selecionado, volume necessário e metadados
    """
    fluido_key = fluido.upper().replace('-', '')
    rho = _RHO_LIQUIDO.get(fluido_key, _RHO_FALLBACK)
    nota_fluido = "" if fluido_key in _RHO_LIQUIDO else f" (densidade de referência R404A)"

    # Volume que o tanque precisa comportar (líquido a ~25°C)
    volume_necessario_l = round(carga_total_kg / rho, 2)

    # Menor tanque cujo volume útil ≥ volume necessário
    selecionado = None
    for tanque in sorted(_TANQUES, key=lambda t: t["volume_total_l"]):
        if tanque["volume_util_l"] >= volume_necessario_l:
            selecionado = tanque
            break

    if selecionado is None:
        # Sistema além da tabela — retorna o maior com aviso
        selecionado = _TANQUES[-1]
        aviso = (
            f"Volume necessário ({volume_necessario_l} L) excede o maior tanque "
            f"da tabela ({selecionado['modelo']} — {selecionado['volume_util_l']} L úteis). "
            "Consultar engenharia para solução com múltiplos tanques."
        )
    else:
        aviso = None

    return {
        "fluido":                fluido,
        "carga_total_kg":        round(carga_total_kg, 2),
        "rho_liquido_kg_l":      rho,
        "volume_necessario_l":   volume_necessario_l,
        "norma":                 "ABNT NBR 16.069 — volume útil = 80% do volume total",
        "tanque": {
            "fabricante":    selecionado["fabricante"],
            "modelo":        selecionado["modelo"],
            "volume_total_l": selecionado["volume_total_l"],
            "volume_util_l":  selecionado["volume_util_l"],
            "conexao":       selecionado["conexao"],
        },
        "aviso":       aviso,
        "nota_fluido": nota_fluido,
    }
