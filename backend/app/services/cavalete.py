"""
Análise do cavalete de componentes — identifica luvas, porcas e reduções
necessárias ao longo da linha de líquido e linha de sucção.

Sequência linha de líquido (condensadora → evaporador):
  Condensadora → [Tanque] → Linha → GBC → Filtro → Solenoide → Visor → VET → Evaporador

Sequência linha de sucção (evaporador → condensadora):
  Evaporador → Trecho → Sifão → Subida → Contra-sifão → Trecho → GBC → Linha → Condensadora

Tipos de acoplamento:
  - Solda:  bitolas iguais → nada (solda direta)
            bitolas diferentes → luva de redução (AxB, maior x menor)
  - Rosca/Flange: sempre porca na bitola do componente (entrada e saída)
  - Luva de passagem: 1 a cada 5 m de tubulação corrida
"""

from __future__ import annotations
import math


def _luvas_passagem(bitola: str, metros: float) -> list[dict]:
    """1 luva de passagem a cada 5 metros de tubulação."""
    qtd = math.floor(metros / 5)
    if qtd <= 0:
        return []
    return [{"item": f"Luva de Passagem {bitola}", "quantidade": qtd,
             "unidade": "un", "detalhe": f"1 a cada 5 m — {metros:.1f} m de tubo",
             "tipo_item": "luva_passagem"}]


def _reducao(de: str, para: str, posicao: str) -> dict | None:
    """Retorna luva de redução se as bitolas forem diferentes."""
    if _normalizar(de) == _normalizar(para):
        return None
    maior, menor = (de, para) if _rank(de) > _rank(para) else (para, de)
    return {"item": f"Luva de Redução {maior} x {menor}", "quantidade": 1,
            "unidade": "un", "detalhe": posicao, "tipo_item": "luva_reducao"}


def _porca(bitola: str, posicao: str) -> dict:
    return {"item": f"Porca {bitola}", "quantidade": 1,
            "unidade": "un", "detalhe": posicao, "tipo_item": "porca"}


# Ordem de tamanho das bitolas padrão
_ORDEM = [
    '3/8"', '1/2"', '5/8"', '3/4"', '7/8"',
    '1.1/8"', '1.3/8"', '1.5/8"', '2.1/8"', '2.5/8"', '3.1/8"',
]


def _normalizar(b: str) -> str:
    return b.strip().replace(' ', '').replace('"', '"').replace('"', '"')


def _rank(b: str) -> int:
    bn = _normalizar(b)
    for i, s in enumerate(_ORDEM):
        if _normalizar(s) == bn:
            return i
    return -1


def _juntar_itens(itens: list[dict]) -> list[dict]:
    """Agrupa itens iguais somando quantidades."""
    agrupado: dict[str, dict] = {}
    for item in itens:
        chave = item["item"]
        if chave in agrupado:
            agrupado[chave]["quantidade"] += item["quantidade"]
        else:
            agrupado[chave] = dict(item)
    return list(agrupado.values())


def analisar_cavalete(
    # ── Equipamentos ──────────────────────────────────────────────────────
    condensadora_cx_liquido: str,   # ex: "3/8\""
    condensadora_cx_succao: str,    # ex: "5/8\""
    evaporador_cx_liquido: str,     # ex: "1/2\""
    evaporador_cx_succao: str,      # ex: "7/8\""
    # ── Bitolas das linhas (Card 4) ───────────────────────────────────────
    diametro_liquido: str,          # bitola da linha de líquido
    diametro_succao: str,           # bitola da linha de sucção
    # ── Componentes do cavalete ───────────────────────────────────────────
    filtro_conexao: str,            # bitola do filtro secador
    filtro_tipo: str,               # 'solda' ou 'rosca'
    solenoide_conexao: str,         # bitola da solenoide (passante)
    visor_conexao: str,             # bitola do visor
    visor_tipo: str,                # 'solda' ou 'rosca'
    vet_entrada: str,               # sempre "3/8\""
    vet_saida: str,                 # sempre "1/2\""
    # ── Comprimentos das linhas ───────────────────────────────────────────
    comprimento_liquido_m: float,
    comprimento_succao_m: float,
    # ── Trechos internos do cavalete (Configurações) ──────────────────────
    trecho_vet_evap_m: float,       # VET → evaporador
    trecho_evap_sifao_m: float,     # evaporador → sifão
    trecho_subida_m: float,         # sifão → contra-sifão
    trecho_sifao_gbc_m: float,      # contra-sifão → GBC sucção
    # ── Tanque de líquido (opcional) ─────────────────────────────────────
    tanque_conexao: str | None = None,
    # ── Flags de inclusão (Configurações) ────────────────────────────────
    incluir_filtro:      bool = True,
    incluir_visor:       bool = True,
    incluir_gbc_entrada: bool = True,
    incluir_gbc_saida:   bool = True,
) -> dict:

    itens_liquido: list[dict] = []
    itens_succao: list[dict] = []

    dl = diametro_liquido
    ds = diametro_succao

    # ══════════════════════════════════════════════════════════════════════
    # LINHA DE LÍQUIDO
    # ══════════════════════════════════════════════════════════════════════

    # 1. Condensadora saída → Tanque (se houver)
    bitola_atual = condensadora_cx_liquido
    if tanque_conexao:
        r = _reducao(bitola_atual, tanque_conexao, "Condensadora → Tanque de Líquido")
        if r: itens_liquido.append(r)
        bitola_atual = tanque_conexao  # tanque é passante

        r = _reducao(bitola_atual, dl, "Tanque de Líquido → Linha")
        if r: itens_liquido.append(r)

    # 2. Linha de líquido corrida (com luvas de passagem)
    itens_liquido += _luvas_passagem(dl, comprimento_liquido_m)

    # 3. Condensadora/Tanque → GBC entrada (se incluir_gbc_entrada)
    origem_linha = condensadora_cx_liquido if not tanque_conexao else tanque_conexao
    if incluir_gbc_entrada:
        r = _reducao(origem_linha, dl, "Condensadora/Tanque → GBC Entrada (linha líquido)")
        if r: itens_liquido.insert(0, r)
        bitola_apos_gbc_entrada = dl
    else:
        r = _reducao(origem_linha, dl, "Condensadora/Tanque → Linha de Líquido")
        if r: itens_liquido.insert(0, r)
        bitola_apos_gbc_entrada = dl

    # Bitola corrente após GBC entrada
    bitola_corrente = bitola_apos_gbc_entrada

    # 4. GBC saída → Filtro (se incluir_filtro)
    if incluir_filtro:
        if filtro_tipo == 'rosca':
            r = _reducao(bitola_corrente, filtro_conexao, "Linha → Filtro Secador")
            if r: itens_liquido.append(r)
            itens_liquido.append(_porca(filtro_conexao, "Entrada Filtro Secador"))
            bitola_corrente = filtro_conexao
        else:
            r = _reducao(bitola_corrente, filtro_conexao, "GBC → Filtro Secador")
            if r: itens_liquido.append(r)
            bitola_corrente = filtro_conexao

    # 5. → Solenoide (sempre presente, passante)
    r = _reducao(bitola_corrente, solenoide_conexao, "Filtro/GBC → Solenoide")
    if r: itens_liquido.append(r)
    bitola_corrente = solenoide_conexao

    # 6. Solenoide → Visor (se incluir_visor)
    if incluir_visor:
        if visor_tipo == 'rosca':
            r = _reducao(bitola_corrente, visor_conexao, "Solenoide → Visor (ajuste linha)")
            if r: itens_liquido.append(r)
            itens_liquido.append(_porca(visor_conexao, "Entrada Visor de Líquido"))
            itens_liquido.append(_porca(visor_conexao, "Saída Visor de Líquido"))
            bitola_corrente = visor_conexao
        else:
            r = _reducao(bitola_corrente, visor_conexao, "Solenoide → Visor de Líquido")
            if r: itens_liquido.append(r)
            bitola_corrente = visor_conexao

    # Filtro rosca — porca de saída (só se filtro incluído e rosca)
    if incluir_filtro and filtro_tipo == 'rosca':
        itens_liquido.append(_porca(filtro_conexao, "Saída Filtro Secador"))

    # 7. → VET (flange + porca, sempre presente)
    r = _reducao(bitola_corrente, vet_entrada, "Componente anterior → VET")
    if r: itens_liquido.append(r)
    itens_liquido.append(_porca(vet_entrada, "Entrada VET (flange)"))
    itens_liquido.append(_porca(vet_saida,  "Saída VET (flange)"))

    # 8. Trecho VET → Evaporador
    itens_liquido += _luvas_passagem(vet_saida, trecho_vet_evap_m)

    # 9. → Evaporador entrada
    r = _reducao(vet_saida, evaporador_cx_liquido, "Trecho VET → Entrada Evaporador")
    if r: itens_liquido.append(r)

    # ══════════════════════════════════════════════════════════════════════
    # LINHA DE SUCÇÃO
    # ══════════════════════════════════════════════════════════════════════

    # 1. Evaporador saída → trecho Evap→Sifão
    # Evaporador saída (evaporador_cx_succao) é o ponto de partida = bitola do tubo de sucção
    # Ajuste se evaporador_cx_succao ≠ ds (raro mas possível)
    r = _reducao(evaporador_cx_succao, ds, "Saída Evaporador → Tubo de Sucção")
    if r: itens_succao.append(r)

    itens_succao += _luvas_passagem(ds, trecho_evap_sifao_m)

    # 2. Sifão (comprado, bitola = ds)
    itens_succao.append({"item": f"Sifão {ds}", "quantidade": 1,
                         "unidade": "un", "detalhe": "Saída do evaporador", "tipo_item": "sifao"})

    # 3. Trecho subida (Sifão → Contra-sifão)
    itens_succao += _luvas_passagem(ds, trecho_subida_m)

    # 4. Contra-sifão (comprado, bitola = ds)
    itens_succao.append({"item": f"Contra-sifão {ds}", "quantidade": 1,
                         "unidade": "un", "detalhe": "Topo da subida", "tipo_item": "contra_sifao"})

    # 5. Trecho Contra-sifão → GBC sucção
    itens_succao += _luvas_passagem(ds, trecho_sifao_gbc_m)

    # 6. GBC sucção (bitola = ds, passante — sem redução, se incluir_gbc_saida)
    # Não gera item adicional pois é passante; a flag controla apenas se consta no orçamento

    # 7. Linha de sucção corrida (com luvas de passagem)
    itens_succao += _luvas_passagem(ds, comprimento_succao_m)

    # 8. Linha → Condensadora entrada (com GBC saída se incluído)
    if incluir_gbc_saida:
        r = _reducao(ds, condensadora_cx_succao, "Linha Sucção → GBC Saída → Condensadora")
    else:
        r = _reducao(ds, condensadora_cx_succao, "Linha Sucção → Condensadora")
    if r: itens_succao.append(r)

    # ══════════════════════════════════════════════════════════════════════
    # CONSOLIDAÇÃO
    # ══════════════════════════════════════════════════════════════════════
    resumo = _juntar_itens(itens_liquido + itens_succao)

    return {
        "linha_liquido": itens_liquido,
        "linha_succao":  itens_succao,
        "resumo":        resumo,
        "configuracao": {
            "tipo_conexao_filtro":  filtro_tipo,
            "tipo_conexao_visor":   visor_tipo,
            "diametro_liquido":     dl,
            "diametro_succao":      ds,
            "incluir_filtro":       incluir_filtro,
            "incluir_visor":        incluir_visor,
            "incluir_gbc_entrada":  incluir_gbc_entrada,
            "incluir_gbc_saida":    incluir_gbc_saida,
        }
    }
