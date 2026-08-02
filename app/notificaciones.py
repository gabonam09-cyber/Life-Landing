"""Aviso por correo cuando entra un lead nuevo.

Dos reglas que rigen este modulo:

1. **El lead ya esta guardado antes de llamar aqui.** Si el correo falla, se
   registra en el log y nada mas: nunca se pierde un prospecto porque el
   servidor de correo tuviera un mal dia.
2. **Se envia en segundo plano.** Una conexion SMTP tarda entre 1 y 5 segundos;
   hacerla dentro de la peticion dejaria a la persona mirando una pagina en
   blanco justo despues de enviar el formulario.
"""

import logging
import smtplib
import ssl
import threading
from email.message import EmailMessage

log = logging.getLogger(__name__)


def _construir_mensaje(cfg, lead):
    msg = EmailMessage()
    msg["Subject"] = f"Nuevo lead: {lead.get('clinica') or lead['nombre']}"
    msg["From"] = cfg["remitente"]
    msg["To"] = cfg["destinatario"]

    # Responder al correo lleva directo al prospecto, sin copiar la direccion.
    if lead.get("email"):
        msg["Reply-To"] = lead["email"]

    msg.set_content(
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
    return msg


def _enviar(cfg, lead):
    try:
        contexto = ssl.create_default_context()
        with smtplib.SMTP(cfg["host"], cfg["puerto"], timeout=20) as smtp:
            smtp.starttls(context=contexto)
            smtp.login(cfg["usuario"], cfg["password"])
            smtp.send_message(_construir_mensaje(cfg, lead))
        log.info("Aviso de lead enviado a %s", cfg["destinatario"])
    except Exception:
        # A proposito se captura todo: un fallo aqui no puede escalar a la
        # peticion, que ya termino y ya guardo el lead.
        log.exception("No se pudo enviar el aviso del lead (el lead SÍ se guardó)")


def avisar_lead_nuevo(app, lead):
    """Manda el aviso en un hilo aparte. `lead` es un dict con datos planos."""
    cfg = {
        "host": app.config.get("SMTP_HOST"),
        "puerto": app.config.get("SMTP_PORT"),
        "usuario": app.config.get("SMTP_USER"),
        "password": app.config.get("SMTP_PASSWORD"),
        "destinatario": app.config.get("NOTIFICAR_A"),
        "remitente": app.config.get("SMTP_USER"),
        "url_panel": app.config.get("URL_PANEL", "/panel"),
    }

    if not (cfg["usuario"] and cfg["password"] and cfg["destinatario"]):
        # Sin credenciales el sitio sigue funcionando: solo no avisa.
        log.warning("Aviso por correo desactivado: faltan SMTP_USER, SMTP_PASSWORD o NOTIFICAR_A")
        return

    threading.Thread(target=_enviar, args=(cfg, lead), daemon=True).start()
