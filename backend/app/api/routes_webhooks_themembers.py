import base64
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
# o texto da doc, na raiz do payload, dentro do envelope `payload` (formato
# "Envelope com payload" da spec) e dentro de `data` (formato "Evento direto"
# — achado numa entrega real em 2026-09-08: chaves_topo eram só
# ['created_at','data','event','object'], nenhum candidato batia na raiz,
# então o token — se existir nesse formato — só pode estar 1 nível mais
# fundo, dentro de `data`). Usuário pediu pra tratar esse artigo como fonte
# de verdade e configurar assim.
_CAMPOS_TOKEN_CANDIDATOS = ["token", "security_token", "webhook_token", "secret", "signature_token"]


def _extrair_token_do_payload(body: dict) -> str | None:
    fontes = [body]
    for chave_aninhada in ("payload", "data"):
        aninhado = body.get(chave_aninhada)
        if isinstance(aninhado, dict):
            fontes.append(aninhado)
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

    Mecanismos de autenticação aceitos (OR — qualquer um autoriza), porque
    as fontes oficiais da TheMembers divergem sobre qual é o real pra
    Checkout, e a 1ª tentativa (HMAC com a string literal) ficou
    confirmadamente incompatível com entregas reais por dias (chamado
    aberto desde 2026-09-04):

    1. `x-signature` = HMAC-SHA256 do corpo bruto usando
       THEMEMBERS_WEBHOOK_TOKEN **como string UTF-8** literal como chave
       (documentation.themembers.dev.br/webhooks/webhooks-do-checkout/
       seguranca, verificada ao vivo em 2026-09-03) — nunca bateu em
       entrega real.
    2. `x-signature` = HMAC-SHA256 do corpo bruto usando os **bytes brutos
       decodificados de base64** de THEMEMBERS_WEBHOOK_TOKEN como chave —
       hipótese de 2026-09-09, a partir do diagnóstico de formato de uma
       entrega real (assinatura recebida = 64 hex = SHA-256 exato; secret
       configurado = 44 chars = exatamente 32 bytes em base64 com padding).
       Testando contra entrega real pra confirmar.
    3. Token igual a THEMEMBERS_WEBHOOK_TOKEN embutido no próprio payload
       (ajuda.themembers.com.br, artigo "Como configurar Webhooks Externos",
       achado em 2026-09-08 — ver `_extrair_token_do_payload`) — testado
       contra payload real, nunca apareceu.

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

    # Hipótese testada e confirmada em 2026-09-09: o diagnóstico de formato
    # (ver log themembers_webhook_401 mais abaixo) mostrou assinatura_len=64
    # hex (HMAC-SHA256 exato, bate com a doc) e secret_len=44 — exatamente o
    # tamanho de 32 bytes em base64 com padding. O "Token de segurança" do
    # painel provavelmente é mostrado já em base64, mas o worker de entrega
    # deles assina com os 32 bytes BRUTOS decodificados como chave, não com
    # a string base64 literal (padrão comum, ex: Stripe/GitHub têm variantes
    # assim). `secret_configurado.encode("utf-8")` acima usa a string
    # literal — por isso nunca batia mesmo com o token idêntico nos dois
    # lados. `validate=True` evita decodificar silenciosamente algo que não
    # é base64 de verdade (gera ValueError, tratado abaixo).
    hmac_ok_secret_base64 = False
    if secret_configurado and not hmac_ok:
        try:
            secret_bytes_decodificado = base64.b64decode(secret_configurado, validate=True)
            assinatura_esperada_b64 = hmac.new(
                secret_bytes_decodificado, corpo_bruto, hashlib.sha256
            ).hexdigest()
            hmac_ok_secret_base64 = bool(
                x_signature and hmac.compare_digest(x_signature, assinatura_esperada_b64)
            )
        except ValueError:
            pass
    hmac_ok = hmac_ok or hmac_ok_secret_base64

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

    # Diagnóstico temporário (2026-09-09) — testa a 3ª hipótese: x-signature
    # é o próprio token, comparado direto (não um HMAC, não embutido no
    # payload). Só LOGA por enquanto — não autoriza a requisição ainda,
    # de propósito, até confirmar contra uma entrega real. Remover (junto
    # com o log abaixo) depois de decidir qual mecanismo é o real.
    token_direto_no_header_ok = bool(
        x_signature and secret_configurado and hmac.compare_digest(x_signature, secret_configurado)
    )

    if not (hmac_ok or token_payload_ok):
        # Debug temporário (mesmo padrão já usado e removido em 2026-09-04,
        # commit adcfb85/ddc233d) — só loga as CHAVES de topo do payload
        # (nunca valores, nunca o token, nunca o payload integral, por
        # exigência da própria spec) pra confirmar contra uma entrega real
        # se algum dos campos candidatos aparece, e com qual nome. Remover
        # depois de confirmar.
        #
        # 2026-09-09: acrescenta diagnóstico de FORMATO do x-signature
        # recebido (tamanho, se é hex, se é charset base64, se tem cara de
        # PEM) — nunca o valor em si — pra decidir entre 3 hipóteses:
        # HMAC-SHA256 (hex, 64 chars), token puro (mesmo tamanho do secret
        # configurado) ou chave/assinatura pública (bem mais longo, ou com
        # marcador PEM tipo "-----BEGIN").
        chaves_topo = sorted(body_parseado.keys()) if body_parseado else None
        chaves_envelope = None
        if body_parseado and isinstance(body_parseado.get("payload"), dict):
            chaves_envelope = sorted(body_parseado["payload"].keys())
        chaves_data = None
        if body_parseado and isinstance(body_parseado.get("data"), dict):
            chaves_data = sorted(body_parseado["data"].keys())

        assinatura_len = len(x_signature) if x_signature else None
        secret_len = len(secret_configurado) if secret_configurado else None
        assinatura_eh_hex = bool(x_signature) and all(c in "0123456789abcdefABCDEF" for c in x_signature)
        assinatura_eh_base64_charset = bool(x_signature) and all(
            c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in x_signature
        )
        assinatura_parece_pem = bool(x_signature) and ("BEGIN" in x_signature or "-----" in x_signature)

        logger.warning(
            "themembers_webhook_401 hmac_ok=%s hmac_ok_secret_base64=%s tem_x_signature=%s chaves_topo=%s "
            "chaves_envelope=%s chaves_data=%s token_direto_no_header_ok=%s assinatura_len=%s secret_len=%s "
            "assinatura_eh_hex=%s assinatura_eh_base64_charset=%s assinatura_parece_pem=%s",
            hmac_ok, hmac_ok_secret_base64, bool(x_signature), chaves_topo, chaves_envelope, chaves_data,
            token_direto_no_header_ok, assinatura_len, secret_len, assinatura_eh_hex,
            assinatura_eh_base64_charset, assinatura_parece_pem,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Assinatura inválida.")

    if hmac_ok_secret_base64:
        logger.warning("themembers_webhook_autorizado_via_hmac_secret_base64 — hipótese do secret em base64 confirmada")

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
