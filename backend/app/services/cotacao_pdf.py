"""Importa cotação recebida em PDF (formato próprio de cada fornecedor) — casamento
por IA em vez de planilha estruturada.

Mesmo relatório de saída que `cotacao_import.casar_itens()` (ok/sem_preco/
nao_encontrado/linha_extra), mais um status novo (`possivel_substituicao`) pra
quando o fornecedor ofertou algo relacionado mas não exatamente o que foi pedido
— a IA nunca decide sozinha nesses casos, só sinaliza pro humano revisar.

Apelidos: pra cada fornecedor, os pares (termo_fornecedor → nosso item) já
confirmados antes são passados como contexto — reduz a IA a resolver só o que
é novidade daquele fornecedor ("cold start"). Ver DESIGN_IMPORTACAO_PDF_COTACAO_2026-09-01.md.
"""
from __future__ import annotations
import base64
import json
import logging

from anthropic import AsyncAnthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

MODELO = "claude-sonnet-5"
TIMEOUT_S = 120.0  # PDF + 20-30 itens pode levar mais que o padrão em dias de API mais lenta

_TOOL = {
    "name": "reportar_casamento_cotacao",
    "description": (
        "Reporta o casamento entre os itens lidos do PDF de cotação do fornecedor "
        "e a nossa lista de itens solicitados."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "itens": {
                "type": "array",
                "description": (
                    "Um resultado para CADA item da nossa lista (mesmo os não encontrados), "
                    "mais uma entrada extra (item_id=null) para cada linha do PDF que não "
                    "corresponde a nenhum item nosso."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "item_id": {
                            "type": ["integer", "null"],
                            "description": "ID do nosso item (da lista fornecida), ou null se for linha extra do PDF",
                        },
                        "status": {
                            "type": "string",
                            "enum": ["ok", "nao_encontrado", "linha_extra", "possivel_substituicao"],
                        },
                        "preco_unitario": {"type": ["number", "null"]},
                        "marca_modelo": {"type": ["string", "null"], "description": "marca/modelo lido no PDF"},
                        "prazo_dias": {"type": ["integer", "null"]},
                        "obs": {
                            "type": ["string", "null"],
                            "description": "observação — obrigatório explicar o motivo quando status=possivel_substituicao",
                        },
                        "descricao_pdf": {
                            "type": ["string", "null"],
                            "description": "a descrição literal lida do PDF para esse item (pra mostrar ao usuário)",
                        },
                        "termo_fornecedor": {
                            "type": ["string", "null"],
                            "description": (
                                "Fragmento canônico da descrição do fornecedor que identifica o TIPO "
                                "do produto, sem medidas/bitolas específicas (ex: 'acumulador de succao', "
                                "não 'acumulador de succao 1.1/8 solda importado'). Só quando item_id != null "
                                "e status é ok ou possivel_substituicao — usado pra aprender o apelido."
                            ),
                        },
                    },
                    "required": ["status"],
                },
            },
        },
        "required": ["itens"],
    },
}


def _prompt(itens_banco: list[dict], apelidos: list[dict]) -> str:
    itens_json = json.dumps(itens_banco, ensure_ascii=False, indent=2)
    apelidos_json = json.dumps(apelidos, ensure_ascii=False, indent=2) if apelidos else "[]"
    return f"""Você vai ler uma cotação em PDF que um fornecedor de refrigeração nos devolveu, e
casar cada linha dela com a nossa lista de itens solicitados.

NOSSA LISTA DE ITENS (id, tipo, descrição, detalhe, qtde, unidade):
{itens_json}

APELIDOS JÁ CONHECIDOS DESTE FORNECEDOR (termo que ELE usa → nosso item — use como forte
indício de casamento quando encontrar algo parecido, mas confirme pelo contexto):
{apelidos_json}

Instruções:
1. Para CADA item da nossa lista, procure a linha correspondente no PDF e reporte:
   - status "ok": achou o mesmo item (ou equivalente claro), com preço.
   - status "possivel_substituicao": o fornecedor ofertou algo relacionado mas
     tecnicamente diferente do que pedimos (marca diferente, componente com função
     parecida mas não idêntica, capacidade diferente) — SEMPRE explique o motivo em
     `obs`, em no máximo 200 caracteres, direto ao ponto (o campo é curto).
     NUNCA classifique como "ok" quando houver dúvida real — prefira sinalizar.
   - status "nao_encontrado": não achou nada relacionado a esse item no PDF.
2. Para cada linha do PDF que NÃO corresponde a nenhum item da nossa lista (o
   fornecedor incluiu algo que não pedimos), reporte item_id=null, status "linha_extra".
3. Preencha `termo_fornecedor` (fragmento genérico, sem medida) sempre que item_id
   não for null e o status for "ok" ou "possivel_substituicao" — é o que vamos
   lembrar pra reconhecer esse fornecedor mais rápido da próxima vez.
4. Preços: leia o preço unitário já com impostos/descontos aplicados quando o PDF
   distinguir isso (preço final que o cliente pagaria por unidade).
5. Nunca invente item_id que não esteja na nossa lista.

Responda chamando a ferramenta `reportar_casamento_cotacao` com o relatório completo."""


def _cliente() -> AsyncAnthropic:
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY não configurada — defina no .env (local) ou nas "
            "variáveis de ambiente do Render (produção) para usar a importação de PDF."
        )
    return AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=TIMEOUT_S)


async def analisar_pdf_cotacao(
    pdf_bytes: bytes,
    itens_banco: list[dict],
    apelidos: list[dict],
) -> list[dict]:
    """Chama Claude com o PDF + nossa lista de itens, retorna o relatório de casamento.

    `itens_banco`: [{"id", "tipo_item", "descricao", "detalhe", "qtde", "unidade"}, ...]
    `apelidos`: [{"termo_fornecedor", "nosso_descricao"}, ...]

    Assíncrona de propósito — chamada de dentro de uma rota async do FastAPI.
    A versão síncrona do cliente Anthropic, chamada direto sem `await`, trava o
    loop de eventos inteiro até a API responder; em produção (WEB_CONCURRENCY=1,
    um processo só) isso deixava o app inteiro sem responder durante a chamada,
    às vezes o bastante pra o Render considerar o processo travado e reiniciar
    no meio da requisição (achado em produção, 2026-09-01).
    """
    client = _cliente()
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    resposta = await client.messages.create(
        model=MODELO,
        max_tokens=8000,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "reportar_casamento_cotacao"},
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64},
                },
                {"type": "text", "text": _prompt(itens_banco, apelidos)},
            ],
        }],
    )

    logger.warning(
        "cotacao_pdf: stop_reason=%s usage=%s blocos=%s",
        resposta.stop_reason, resposta.usage,
        [b.type for b in resposta.content],
    )

    bloco = next((b for b in resposta.content if b.type == "tool_use"), None)
    if not bloco:
        raise RuntimeError("A IA não retornou um resultado estruturado — tente novamente.")

    itens_ia = bloco.input.get("itens", [])
    logger.warning(
        "cotacao_pdf: %d itens brutos recebidos, tipos=%s, %d itens no nosso lado",
        len(itens_ia), [type(x).__name__ for x in itens_ia[:10]], len(itens_banco),
    )
    banco_por_id = {i["id"]: i for i in itens_banco}
    relatorio: list[dict] = []
    vistos: set[int] = set()

    def _obs(texto):
        # Salvaguarda — o prompt já pede <=200 chars, mas obs_fornecedor no banco é
        # 500 (ver migration 0031); nunca deixar a IA estourar a coluna.
        return texto[:490] if texto else texto

    for it in itens_ia:
        if not isinstance(it, dict):
            # A IA às vezes devolve um elemento fora do formato pedido, mesmo com
            # saída estruturada forçada — ignora esse item pontual em vez de
            # derrubar a análise inteira (achado em produção, 2026-09-01).
            continue
        item_id = it.get("item_id")
        if item_id is not None and item_id in banco_por_id:
            vistos.add(item_id)
            base = banco_por_id[item_id]
            relatorio.append({
                "item_id": item_id,
                "descricao": base["descricao"],
                "qtde": base["qtde"],
                "unidade": base["unidade"],
                "status": it.get("status", "nao_encontrado"),
                "preco_unitario": it.get("preco_unitario"),
                "preco_bruto": None,
                "marca_modelo": it.get("marca_modelo"),
                "prazo_dias": it.get("prazo_dias"),
                "obs": _obs(it.get("obs")),
                "descricao_pdf": it.get("descricao_pdf"),
                "termo_fornecedor": it.get("termo_fornecedor"),
            })
        else:
            # Linha extra do PDF (ou item_id que a IA não deveria ter inventado — cai aqui também)
            relatorio.append({
                "item_id": None,
                "descricao": it.get("descricao_pdf") or "(sem descrição)",
                "qtde": 1,
                "unidade": "un",
                "status": "linha_extra",
                "preco_unitario": it.get("preco_unitario"),
                "preco_bruto": None,
                "marca_modelo": it.get("marca_modelo"),
                "prazo_dias": it.get("prazo_dias"),
                "obs": _obs(it.get("obs")),
                "descricao_pdf": it.get("descricao_pdf"),
                "termo_fornecedor": None,
            })

    # Itens nossos que a IA não mencionou de jeito nenhum → não encontrado
    for item_id, base in banco_por_id.items():
        if item_id not in vistos:
            relatorio.append({
                "item_id": item_id,
                "descricao": base["descricao"],
                "qtde": base["qtde"],
                "unidade": base["unidade"],
                "status": "nao_encontrado",
                "preco_unitario": None,
                "preco_bruto": None,
                "marca_modelo": None,
                "prazo_dias": None,
                "obs": None,
                "descricao_pdf": None,
                "termo_fornecedor": None,
            })

    return relatorio
