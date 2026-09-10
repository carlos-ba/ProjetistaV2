import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db
from app.services.webhook_themembers import processar_webhook

router = APIRouter(prefix="/api/webhooks/themembers", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/checkout", status_code=status.HTTP_200_OK)
async def receber_webhook_checkout(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Webhook do Checkout TheMembers/TheBank.

    SEM validação de assinatura/token — decisão consciente do usuário em
    2026-09-10, pra desbloquear o cliente pago parado enquanto o mecanismo
    real de assinatura da TheMembers continua desconhecido. 5 mecanismos
    testados contra entregas reais (HMAC string literal, HMAC secret em
    base64, token puro no header, token embutido no payload, webhook/secret
    100% novo) — nenhum bateu (histórico completo em CLAUDE.md, seção
    "Webhook do Checkout TheMembers", e na memória do projeto). Endpoint
    aberto de propósito: aceita qualquer payload POST, sem checar
    `x-signature` nem nenhum token. Revisar quando a TheMembers responder
    o chamado com o mecanismo real de assinatura.

    Único gate que permanece: `THEMEMBERS_WEBHOOK_ENABLED`, kill-switch
    operacional (não é validação de origem/autenticidade) — permite
    desligar o processamento via env var no Render sem precisar de deploy.
    """
    if not settings.THEMEMBERS_WEBHOOK_ENABLED:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Webhook desabilitado.")

    corpo_bruto = await request.body()
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
