"""Aviso por correo cuando entra un lead nuevo.

Hay dos vías de envío y se elige sola la que esté configurada:

1. **API HTTP (Resend).** La recomendada. Viaja por el puerto 443, que es
   tráfico web normal. Es la única que funciona en el plan gratuito de Render:
   desde septiembre de 2025 bloquea el tráfico saliente a los puertos SMTP
   (25, 465 y 587), así que un envío por SMTP se queda colgado hasta agotar el
   tiempo de espera. Ver:
   https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports
2. **SMTP.** Solo sirve en local o si el servicio pasa a un plan de pago.

Dos reglas que rigen el modulo, en cualquiera de las dos vías:

- **El lead ya esta guardado antes de llamar aqui.** Si el correo falla, se
  registra en el log y nada mas: nunca se pierde un prospecto porque el
  servidor de correo tuviera un mal dia.
- **Se envia en segundo plano**, para no dejar a la persona esperando despues
  de darle a enviar.
"""

import json
import logging
import smtplib
import ssl
import threading
import urllib.error
import urllib.request
from email.message import EmailMessage

log = logging.getLogger(__name__)

API_RESEND = "https://api.resend.com/emails"


def _asunto(lead):
    return f"Nuevo lead: {lead.get('clinica') or lead['nombre']}"


def _cuerpo(cfg, lead):
    return (
        "Alguien pidió una reunión desde la landing.\n\n"
        f"Clínica o spa : {lead.get('clinica') or '—'}\n"
        f"Nombre        : {lead['nombre']}\n"
        f"WhatsApp      : {lead.get('telefono') or '—'}\n"
        f"Correo        : {lead['email']}\n"
        f"Recibido      : {lead['creado_en']}\n\n"
        "Qué escribió:\n"
        f"{lead['mensaje']}\n\n"
        "---\n"
        "Responde a este correo para contestarle directamente.\n"
        f"Todos los leads: {cfg['url_panel']}\n"
    )


def _enviar_por_api(cfg, lead):
    """Envia con la API HTTP de Resend (puerto 443, no bloqueado)."""
    payload = {
        "from": cfg["remitente_api"],
        "to": [cfg["destinatario"]],
        "subject": _asunto(lead),
        "text": _cuerpo(cfg, lead),
    }
    # Responder al correo lleva directo al prospecto, sin copiar la direccion.
    if lead.get("email"):
        payload["reply_to"] = lead["email"]

    peticion = urllib.request.Request(
        API_RESEND,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(peticion, timeout=20) as resp:
        if resp.status >= 300:
            raise RuntimeError(f"Resend respondió {resp.status}")
    log.info("Aviso de lead enviado por API a %s", cfg["destinatario"])


def _enviar_por_smtp(cfg, lead):
    """Alternativa por SMTP. En el plan gratuito de Render esto NO funciona."""
    msg = EmailMessage()
    msg["Subject"] = _asunto(lead)
    msg["From"] = cfg["usuario"]
    msg["To"] = cfg["destinatario"]
    if lead.get("email"):
        msg["Reply-To"] = lead["email"]
    msg.set_content(_cuerpo(cfg, lead))

    contexto = ssl.create_default_context()
    with smtplib.SMTP(cfg["host"], cfg["puerto"], timeout=20) as smtp:
        smtp.starttls(context=contexto)
        smtp.login(cfg["usuario"], cfg["password"])
        smtp.send_message(msg)
    log.info("Aviso de lead enviado por SMTP a %s", cfg["destinatario"])


def _despachar(cfg, lead):
    try:
        if cfg["api_key"]:
            _enviar_por_api(cfg, lead)
        else:
            _enviar_por_smtp(cfg, lead)
    except urllib.error.HTTPError as e:
        # El cuerpo de la respuesta dice exactamente que rechazo Resend.
        detalle = e.read().decode("utf-8", "replace")[:400]
        log.error("Resend rechazó el envío (%s): %s", e.code, detalle)
    except Exception:
        # A proposito se captura todo: un fallo aqui no puede escalar a la
        # peticion, que ya termino y ya guardo el lead.
        log.exception("No se pudo enviar el aviso del lead (el lead SÍ se guardó)")


def avisar_lead_nuevo(app, lead):
    """Manda el aviso en un hilo aparte. `lead` es un dict con datos planos."""
    cfg = {
        "api_key": app.config.get("RESEND_API_KEY"),
        "remitente_api": app.config.get("REMITENTE_API"),
        "host": app.config.get("SMTP_HOST"),
        "puerto": app.config.get("SMTP_PORT"),
        "usuario": app.config.get("SMTP_USER"),
        "password": app.config.get("SMTP_PASSWORD"),
        "destinatario": app.config.get("NOTIFICAR_A"),
        "url_panel": app.config.get("URL_PANEL", "/panel"),
    }

    if not cfg["destinatario"]:
        log.warning("Aviso por correo desactivado: falta NOTIFICAR_A")
        return

    if not cfg["api_key"] and not (cfg["usuario"] and cfg["password"]):
        log.warning(
            "Aviso por correo desactivado: configura RESEND_API_KEY "
            "(recomendado) o SMTP_USER y SMTP_PASSWORD"
        )
        return

    threading.Thread(target=_despachar, args=(cfg, lead), daemon=True).start()
