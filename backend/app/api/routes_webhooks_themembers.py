import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db
from app.services.webhook_themembers import processar_webhook

router = APIRouter(prefix="/api/webhooks/themembers", tags=["webhooks"])
logger = logging.getLogger(__name__)

# Achado em 2026-09-08: o artigo de ajuda oficial da TheMembers sobre
# webhooks externos do Checkout (ajuda.themembers.com.br) descreve um
# mecanismo diferente do documentado em documentation.themembers.dev.br
# (que é o que implementamos abaixo, HMAC-SHA256 em x-signature) — segundo
# esse artigo, o "Token de segurança" normalmente "é informado ao destino e
# enviado no payload do webhook". Nome exato do campo não documentado
# publicamente em nenhum dos dois — checa os candidatos mais plausíveis dado
# o texto da doc, tanto na raiz do payload quanto dentro do envelope
# `payload` (formato "Envelope com payload" da spec). Usuário pediu pra
# tratar esse artigo como fonte de verdade e configurar assim.
_CAMPOS_TOKEN_CANDIDATOS = ["token", "security_token", "webhook_token", "secret", "signature_token"]


def _extrair_token_do_payload(body: dict) -> str | None:
    fontes = [body]
    envelope = body.get("payload")
    if isinstance(envelope, dict):
        fontes.append(envelope)
    for fonte in fontes:
        for campo in _CAMPOS_TOKEN_CANDIDATOS:
            valor = fonte.get(campo)
            if isinstance(valor, str) and valor:
                return valor
    return None


@router.post("/checkout", status_code=status.HTTP_200_OK)
async def receber_webhook_checkout(
    request: Request,
    x_signature: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Webhook do Checkout TheMembers/TheBank.

    Dois mecanismos de autenticação aceitos (OR — qualquer um dos dois
    autoriza), porque as duas fontes oficiais da TheMembers divergem sobre
    qual é o real pra Checkout e a 1ª segue confirmadamente incompatível com
    entregas reais (chamado aberto desde 2026-09-04, causa raiz nunca
    confirmada do lado deles):

    1. `x-signature` = HMAC-SHA256 do corpo bruto usando
       THEMEMBERS_WEBHOOK_TOKEN como secret (documentation.themembers.dev.br/
       webhooks/webhooks-do-checkout/seguranca, verificada ao vivo em
       2026-09-03).
    2. Token igual a THEMEMBERS_WEBHOOK_TOKEN embutido no próprio payload
       (ajuda.themembers.com.br, artigo "Como configurar Webhooks Externos",
       achado em 2026-09-08 — ver `_extrair_token_do_payload`).

    Sem JWT de propósito — provedor externo não carrega sessão de usuário.
    """
    secret_configurado = settings.THEMEMBERS_WEBHOOK_TOKEN
    corpo_bruto = await request.body()

    assinatura_esperada = (
        hmac.new(secret_configurado.encode("utf-8"), corpo_bruto, hashlib.sha256).hexdigest()
        if secret_configurado
        else None
    )
    hmac_ok = bool(assinatura_esperada and x_signature and hmac.compare_digest(x_signature, assinatura_esperada))

    body_parseado: dict | None = None
    if not hmac_ok:
        try:
            body_tentativa = json.loads(corpo_bruto)
            if isinstance(body_tentativa, dict):
                body_parseado = body_tentativa
        except json.JSONDecodeError:
            pass

    token_payload_ok = False
    if not hmac_ok and body_parseado is not None and secret_configurado:
        token_do_payload = _extrair_token_do_payload(body_parseado)
        token_payload_ok = bool(token_do_payload and hmac.compare_digest(token_do_payload, secret_configurado))

    if not (hmac_ok or token_payload_ok):
        # Debug temporário (mesmo padrão já usado e removido em 2026-09-04,
        # commit adcfb85/ddc233d) — só loga as CHAVES de topo do payload
        # (nunca valores, nunca o token, nunca o payload integral, por
        # exigência da própria spec) pra confirmar contra uma entrega real
        # se algum dos campos candidatos aparece, e com qual nome. Remover
        # depois de confirmar.
        chaves_topo = sorted(body_parseado.keys()) if body_parseado else None
        chaves_envelope = None
        if body_parseado and isinstance(body_parseado.get("payload"), dict):
            chaves_envelope = sorted(body_parseado["payload"].keys())
        logger.warning(
            "themembers_webhook_401 hmac_ok=%s tem_x_signature=%s chaves_topo=%s chaves_envelope=%s",
            hmac_ok, bool(x_signature), chaves_topo, chaves_envelope,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Assinatura inválida.")

    if token_payload_ok:
        logger.warning("themembers_webhook_autorizado_via_token_no_payload — mecanismo alternativo confirmado")

    # Trava real da Etapa 1 (achado na revisão de código: validar_producao() só
    # cobre consistência de config no startup, não impedia a rota de processar
    # de verdade se o token fosse configurado antes da hora). Fica DEPOIS da
    # checagem de token de propósito — o passo de deploy da spec (§18.6) exige
    # confirmar que token ausente/incorreto retorna 401 mesmo desabilitado.
    if not settings.THEMEMBERS_WEBHOOK_ENABLED:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Webhook desabilitado.")

    try:
        body = body_parseado if body_parseado is not None else json.loads(corpo_bruto)
        if not isinstance(body, dict):
            raise ValueError("Corpo do webhook precisa ser um objeto JSON.")
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="JSON inválido ou contrato não reconhecido.")

    try:
        registro = await processar_webhook(db, body, corpo_bruto)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Contrato do evento não reconhecido.")

    # Processamento é só transacional — nunca chama API externa/e-mail aqui
    # (spec §5). Toda combinação de status_processamento responde 200: o
    # provedor só precisa saber que recebemos, o estado fica auditável na
    # tabela pra diagnóstico administrativo.
    return {"recebido": True, "status": registro.status_processamento}
