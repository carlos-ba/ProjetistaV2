"""Normalização de texto pra casamento de itens por descrição.

Extraído de `app/services/cotacao_import.py` (`casar_itens()`) pra ser reutilizável —
o mesmo casamento por descrição normalizada agora também é usado pela lista de preços
por empresa (`app/services/produto_empresa.py`), já que nem todo item do orçamento
carrega um id estável de catálogo (painéis, portas, materiais extras do gabinete).
"""
import re


def norm(s: str | None) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip().lower())
