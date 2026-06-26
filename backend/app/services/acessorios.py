"""
Seleção automática de filtro secador e visor de líquido Danfoss.

Lógica de seleção:
  - Diâmetro da linha de líquido: reaproveitado de calculos_tubulacao._selecionar_liquido
  - Filtro secador:
      DML  → sistema COM tanque de líquido (filtro standalone, 100% peneira molecular)
      DMC  → sistema SEM tanque de líquido (filtro + receptor combinados)
  - Visor de líquido: modelo SGN (com indicador de umidade, solda brasada)
      Seleção exclusivamente pelo diâmetro da linha de líquido

Fontes:
  Danfoss Design Center / CoolSelector2 v5.6.13 / pesquisa 2026-06-25
"""

from app.services.calculos_tubulacao import _selecionar_liquido

# ── Tabela DML — filtro secador standalone (sistema COM tanque de líquido) ──
# Usa o maior modelo disponível para cada conexão (maior volume = maior capacidade
# de secagem — recomendação Danfoss para refrigeração comercial)
# Nomenclatura: DML XY → X = volume em in³, Y = código conexão (Y/8 = polegadas)
_FILTRO_DML: dict[str, dict] = {
    '1/4"':   {"modelo": "DML 33",   "volume_in3": 3,  "conexao": '1/4"',   "tipo": "DML"},
    '3/8"':   {"modelo": "DML 163",  "volume_in3": 16, "conexao": '3/8"',   "tipo": "DML"},
    '1/2"':   {"modelo": "DML 304",  "volume_in3": 30, "conexao": '1/2"',   "tipo": "DML"},
    '5/8"':   {"modelo": "DML 485",  "volume_in3": 48, "conexao": '5/8"',   "tipo": "DML"},
    '7/8"':   {"modelo": "DML 307",  "volume_in3": 30, "conexao": '7/8"',   "tipo": "DML"},
    '1.1/8"': {"modelo": "DML 488",  "volume_in3": 48, "conexao": '1.1/8"', "tipo": "DML"},
    '1.3/8"': {"modelo": "DML 4812", "volume_in3": 48, "conexao": '1.3/8"', "tipo": "DML"},
}

# ── Tabela DMC — filtro + receptor combinado (sistema SEM tanque de líquido) ──
# DMC disponível apenas para linhas pequenas (até 1/2").
# Para linhas maiores, mesmo sem tanque, usar DML (sistema já é grande o suficiente
# para justificar um tanque separado — alertar o técnico).
_FILTRO_DMC: dict[str, dict] = {
    '1/4"': {"modelo": "DMC 10",  "volume_in3": 10, "conexao": '1/4"', "tipo": "DMC"},
    '3/8"': {"modelo": "DMC 20",  "volume_in3": 20, "conexao": '3/8"', "tipo": "DMC"},
    '1/2"': {"modelo": "DMC 30",  "volume_in3": 30, "conexao": '1/2"', "tipo": "DMC"},
}

# ── Tabela SGN — visor de líquido com indicador de umidade (solda brasada) ──
# Sufixo "s" = conexão solder (ODF). Posição: depois do filtro, antes da VET.
_VISOR_SGN: dict[str, str] = {
    '1/4"':   "SGN 6s",
    '3/8"':   "SGN 10s",
    '1/2"':   "SGN 12s",
    '5/8"':   "SGN 16s",
    '3/4"':   "SGN 19s",
    '7/8"':   "SGN 22s",
    '1.1/8"': "SGN 22s",   # maior disponível na família SGN
    '1.3/8"': "SGN 22s",
}

# Fluidos com tabela própria de líquido (lista de calculos_tubulacao)
_FLUIDOS_LIQUIDO = {"R22", "R404A"}


def selecionar_acessorios(
    fluido: str,
    capacidade_kcalh: float,
    tem_tanque_liquido: bool = True,
) -> dict:
    """
    Seleciona filtro secador e visor de líquido com base no fluido, capacidade
    e presença de tanque de líquido no projeto.

    Args:
        fluido:             R404A, R22 (outros usam R22 como referência)
        capacidade_kcalh:   carga térmica em kcal/h
        tem_tanque_liquido: True → DML; False → DMC (ou DML com aviso p/ linhas grandes)

    Returns:
        dict com filtro_secador, visor_liquido e metadados de seleção
    """
    fluido_upper = fluido.upper()
    fluido_tabela = fluido_upper if fluido_upper in _FLUIDOS_LIQUIDO else "R22"
    nota_fluido = "" if fluido_upper in _FLUIDOS_LIQUIDO else f" (referência R22)"

    # ── Diâmetro da linha de líquido (mesma lógica do Card 5) ────────────────
    diam_liquido = _selecionar_liquido(fluido_tabela, capacidade_kcalh, fator=1.0)

    # ── Filtro secador ────────────────────────────────────────────────────────
    aviso_filtro = None

    if tem_tanque_liquido:
        filtro_info = _FILTRO_DML.get(diam_liquido)
        tipo_filtro = "DML"
        motivo_tipo = "Sistema com tanque de líquido — filtro standalone"
    else:
        filtro_info = _FILTRO_DMC.get(diam_liquido)
        tipo_filtro = "DMC"
        motivo_tipo = "Sistema sem tanque de líquido — filtro+receptor combinado"
        if filtro_info is None:
            # Linha grande demais para DMC — usar DML e avisar
            filtro_info = _FILTRO_DML.get(diam_liquido)
            tipo_filtro = "DML"
            aviso_filtro = (
                f"Linha {diam_liquido} e grande para DMC. "
                "Sistema deste porte recomenda tanque de liquido separado. "
                "Selecionado DML como alternativa."
            )

    if filtro_info is None:
        filtro_info = {"modelo": "Consultar Engenharia", "volume_in3": None,
                       "conexao": diam_liquido, "tipo": tipo_filtro}

    filtro_resultado = {
        "modelo":       filtro_info["modelo"],
        "fabricante":   "Danfoss",
        "tipo":         filtro_info["tipo"],
        "conexao":      filtro_info["conexao"],
        "volume_in3":   filtro_info.get("volume_in3"),
        "motivo":       motivo_tipo,
        "aviso":        aviso_filtro,
    }

    # ── Visor de líquido ──────────────────────────────────────────────────────
    modelo_visor = _VISOR_SGN.get(diam_liquido, "SGN 22s")

    visor_resultado = {
        "modelo":     modelo_visor,
        "fabricante": "Danfoss",
        "conexao":    diam_liquido,
        "tipo":       "Com indicador de umidade (verde→amarelo)",
        "posicao":    "Após filtro secador, antes da VET",
    }

    return {
        "fluido":              fluido,
        "capacidade_kcalh":    round(capacidade_kcalh),
        "diametro_liquido":    diam_liquido,
        "nota_fluido":         nota_fluido,
        "tem_tanque_liquido":  tem_tanque_liquido,
        "filtro_secador":      filtro_resultado,
        "visor_liquido":       visor_resultado,
    }
