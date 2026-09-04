import hashlib
import hmac
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db
from app.services.webhook_themembers import processar_webhook

router = APIRouter(prefix="/api/webhooks/themembers", tags=["webhooks"])


@router.post("/checkout", status_code=status.HTTP_200_OK)
async def receber_webhook_checkout(
    request: Request,
    x_signature: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Webhook do Checkout TheMembers/TheBank — `x-signature` é um HMAC-SHA256
    do corpo bruto usando THEMEMBERS_WEBHOOK_TOKEN como secret (confirmado na
    documentação oficial, documentation.themembers.dev.br/webhooks/webhooks-do-checkout/seguranca,
    verificada ao vivo em 2026-09-03 — corrige a suposição original da spec de
    token estático comparado direto, que só vale pra Área de Membros, sistema
    diferente).

    Sem JWT de propósito — provedor externo não carrega sessão de usuário.
    """
    secret_configurado = settings.THEMEMBERS_WEBHOOK_TOKEN
    corpo_bruto = await request.body()
    assinatura_esperada = (
        hmac.new(secret_configurado.encode("utf-8"), corpo_bruto, hashlib.sha256).hexdigest()
        if secret_configurado
        else None
    )
    if not assinatura_esperada or not x_signature or not hmac.compare_digest(x_signature, assinatura_esperada):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Assinatura inválida.")

    # Trava real da Etapa 1 (achado na revisão de código: validar_producao() só
    # cobre consistência de config no startup, não impedia a rota de processar
    # de verdade se o token fosse configurado antes da hora). Fica DEPOIS da
    # checagem de token de propósito — o passo de deploy da spec (§18.6) exige
    # confirmar que token ausente/incorreto retorna 401 mesmo desabilitado.
    if not settings.THEMEMBERS_WEBHOOK_ENABLED:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Webhook desabilitado.")

    try:
        body = json.loads(corpo_bruto)
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
