"""
Serviço de envio de email via SMTP (aiosmtplib).
Suporta verificação de conta e recuperação de senha.
"""
import logging
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _enviar_email(destinatario: str, assunto: str, corpo_html: str) -> None:
    """Envia um email HTML via SMTP assíncrono."""
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        logger.warning("Email não configurado — pulando envio para %s", destinatario)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = settings.MAIL_FROM
    msg["To"] = destinatario
    msg.attach(MIMEText(corpo_html, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.MAIL_SERVER,
            port=settings.MAIL_PORT,
            username=settings.MAIL_USERNAME,
            password=settings.MAIL_PASSWORD,
            start_tls=settings.MAIL_STARTTLS,
            use_tls=settings.MAIL_SSL_TLS,
        )
        logger.info("Email enviado para %s", destinatario)
    except Exception as exc:
        logger.error("Falha ao enviar email para %s: %s", destinatario, exc)
        raise


async def enviar_verificacao_email(destinatario: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/verificar-email?token={token}"
    corpo = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2 style="color:#6d28d9">Projetista 360 — Confirme seu email</h2>
      <p>Olá! Clique no botão abaixo para ativar sua conta:</p>
      <a href="{link}"
         style="display:inline-block;background:#6d28d9;color:#fff;padding:12px 28px;
                border-radius:6px;text-decoration:none;font-weight:bold">
        Verificar Email
      </a>
      <p style="color:#888;font-size:12px;margin-top:24px">
        Link válido por 24 horas. Se não se cadastrou, ignore este email.
      </p>
    </body></html>
    """
    await _enviar_email(destinatario, "Projetista 360 — Confirme seu email", corpo)


async def enviar_reset_senha(destinatario: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/redefinir-senha?token={token}"
    corpo = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2 style="color:#6d28d9">Projetista 360 — Redefinição de senha</h2>
      <p>Recebemos uma solicitação para redefinir sua senha. Clique abaixo:</p>
      <a href="{link}"
         style="display:inline-block;background:#6d28d9;color:#fff;padding:12px 28px;
                border-radius:6px;text-decoration:none;font-weight:bold">
        Redefinir Senha
      </a>
      <p style="color:#888;font-size:12px;margin-top:24px">
        Link válido por 1 hora. Se não solicitou, ignore este email.
      </p>
    </body></html>
    """
    await _enviar_email(destinatario, "Projetista 360 — Redefinição de senha", corpo)
