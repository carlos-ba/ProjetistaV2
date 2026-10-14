"""Redação por IA do descritivo técnico da proposta (beta fechado — flag
`Empresa.ia_descritivo_habilitado`, ligado pelo superadmin).

A IA recebe SÓ fatos já calculados pelo sistema (as seções do descritivo de modelo
fixo montadas no frontend: objetivo, premissas, resultado da carga, solução,
motivo da divisão em unidades, margem, observações) e só faz a redação — não pode
acrescentar número, modelo, norma, garantia, preço nem motivo que não estejam nos
fatos. Mesmo assim o texto vai com o nome do técnico pro cliente dele, então:

  * `numeros_fora_dos_fatos()` confere, de forma determinística, se algum número
    escrito pela IA não existe nos fatos — vira aviso na tela (o técnico revisa);
  * o texto nunca é aplicado sozinho: o frontend mostra lado a lado com a versão de
    modelo fixo e só entra na proposta se o técnico escolher (e pode editar).
"""
from __future__ import annotations

import logging
import re

from anthropic import AsyncAnthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

MODELO = "claude-sonnet-5-5"
TIMEOUT_S = 60.0
MAX_TOKENS = 1200

_SISTEMA = """Você redige o descritivo técnico de propostas de câmaras frigoríficas, em português do Brasil.

REGRAS OBRIGATÓRIAS
1. Use SOMENTE os fatos fornecidos. Não invente nem deduza nada: nenhum número, modelo, fabricante, norma, garantia, prazo, preço, vantagem, motivo ou finalidade que não esteja nos fatos. Em especial, não diga que a câmara é para "armazenamento", "resfriamento", "congelamento" ou similar se os fatos não dizem isso — repita apenas o que consta (ex.: "para <produto>").
2. Reproduza todo valor numérico exatamente como está nos fatos (mesmos dígitos, mesma unidade, mesma vírgula decimal).
3. Se os fatos trazem o motivo da divisão em unidades, mantenha esse motivo com o mesmo sentido; se não trazem, não explique a divisão.
4. Tom técnico, claro e objetivo, de engenheiro para cliente. Sem adjetivos de marketing, sem promessas.
5. Entre 3 e 5 parágrafos curtos, separados por uma linha em branco. Sem títulos, sem listas, sem markdown, sem emojis.
6. Responda apenas com o texto do descritivo, sem comentários antes ou depois."""


def _cliente() -> AsyncAnthropic:
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY não configurada — defina no .env (local) ou nas "
            "variáveis de ambiente do Render (produção) para usar a redação por IA."
        )
    return AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=TIMEOUT_S)


def _fatos_em_texto(secoes: list[dict]) -> str:
    blocos = []
    for s in secoes:
        titulo = (s.get("titulo") or "").strip()
        linhas = [p.strip() for p in s.get("paragrafos", []) if p and p.strip()]
        if linhas:
            blocos.append(f"## {titulo}\n" + "\n".join(f"- {l}" for l in linhas))
    return "\n\n".join(blocos)


_RE_NUM = re.compile(r"\d[\d.,]*\d|\d")


def _normalizar_numero(txt: str) -> str:
    """'4.369' / '4,369' / '10,0' → só dígitos significativos para comparar sem se
    importar com o separador (a IA pode trocar '.' por ',' ou omitir '.0')."""
    t = txt.strip(".,")
    # parte decimal "x,0"/"x.0" não muda o valor
    t = re.sub(r"[.,]0+$", "", t)
    return re.sub(r"[.,]", "", t)


def numeros_fora_dos_fatos(texto: str, fatos: str) -> list[str]:
    """Números do `texto` que não aparecem nos `fatos` (comparação por dígitos).

    Inteiros de 1 dígito são ignorados — a IA escreve "duas unidades", "1 circuito"
    etc. sem que isso seja um valor técnico novo."""
    conhecidos = {_normalizar_numero(n) for n in _RE_NUM.findall(fatos)}
    fora: list[str] = []
    for n in _RE_NUM.findall(texto):
        if len(n) == 1:
            continue
        if _normalizar_numero(n) not in conhecidos and n not in fora:
            fora.append(n)
    return fora


async def gerar_descritivo_ia(secoes: list[dict]) -> tuple[str, list[str]]:
    """Devolve (texto, números fora dos fatos). Assíncrona de propósito — ver o
    comentário em `cotacao_pdf.analisar_pdf_cotacao` (cliente síncrono travava o app)."""
    fatos = _fatos_em_texto(secoes)
    if not fatos:
        raise ValueError("Sem fatos para redigir o descritivo.")

    resposta = await _cliente().messages.create(
        model=MODELO,
        max_tokens=MAX_TOKENS,
        system=_SISTEMA,
        messages=[{"role": "user", "content": f"FATOS DO PROJETO\n\n{fatos}\n\nRedija o descritivo técnico."}],
    )
    logger.warning("ia_descritivo: stop_reason=%s usage=%s", resposta.stop_reason, resposta.usage)

    texto = "".join(b.text for b in resposta.content if b.type == "text").strip()
    if not texto:
        raise RuntimeError("A IA não retornou texto — tente novamente.")
    return texto, numeros_fora_dos_fatos(texto, fatos)
