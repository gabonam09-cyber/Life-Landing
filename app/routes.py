import os

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from .extensions import limiter
from .forms import ContactForm, LoginForm
from .models import Lead, db
from .security import login_requerido

bp = Blueprint("main", __name__)

# Pasos del proceso (linea de tiempo del home). Copys provisionales: el cliente
# los reemplazara. Las imagenes se cargan en static/img/paso-0N.jpg cuando esten.
PASOS = [
    {
        "n": "01",
        "titulo": "Diagnóstico inicial",
        "texto": "Revisamos tu negocio, tu oferta y cómo te encuentran hoy tus clientes.",
    },
    {
        "n": "02",
        "titulo": "Auditoría comercial",
        "texto": "Analizamos por dónde entran los mensajes, quién responde y en cuánto tiempo.",
    },
    {
        "n": "03",
        "titulo": "Detectamos la fuga",
        "texto": "Identificamos el punto exacto donde se están perdiendo los clientes.",
    },
    {
        "n": "04",
        "titulo": "Diseñamos el sistema",
        "texto": "Definimos qué necesitas: captación, respuesta con IA, reputación o una combinación.",
    },
    {
        "n": "05",
        "titulo": "Seguimiento continuo",
        "texto": "Cada semana revisamos respuestas, citas agendadas y qué mover a continuación.",
    },
]


# Preguntas frecuentes del home. Copys provisionales: escritos solo con lo que ya
# afirmamos en el sitio (diagnostico gratuito, seleccion de clientes, los 3 sistemas).
FAQS = [
    {
        "n": "01",
        "pregunta": "¿life es una agencia de marketing o algo más?",
        "respuesta": (
            "Combinamos marketing digital con inteligencia artificial aplicada. No vendemos "
            "campañas sueltas: construimos sistemas de captación, respuesta y reputación que "
            "trabajan juntos."
        ),
    },
    {
        "n": "02",
        "pregunta": "¿Qué revisan en el diagnóstico?",
        "respuesta": (
            "Cómo te encuentran hoy tus clientes, por dónde entran los mensajes, cuánto tardas "
            "en responder y qué dicen tus reseñas. Con eso ubicamos dónde se están perdiendo "
            "los clientes."
        ),
    },
    {
        "n": "03",
        "pregunta": "¿Qué pasa después de solicitar el diagnóstico?",
        "respuesta": (
            "Te contactamos en menos de 24 horas para agendar una llamada. Ahí revisamos tu "
            "negocio y, si vemos una oportunidad real de mejora, te proponemos cómo avanzar."
        ),
    },
    {
        "n": "04",
        "pregunta": "¿Trabajan con cualquier negocio?",
        "respuesta": (
            "No. Primero evaluamos si existe una oportunidad real de ayudar. Si no la vemos, "
            "te lo decimos y no avanzamos."
        ),
    },
    {
        "n": "05",
        "pregunta": "¿El diagnóstico tiene costo?",
        "respuesta": (
            "No. El diagnóstico inicial es gratuito y sin compromiso. Solo hablamos de trabajar "
            "juntos si encontramos algo concreto que mejorar."
        ),
    },
    {
        "n": "06",
        "pregunta": "¿Pueden trabajar con mi equipo actual?",
        "respuesta": (
            "Sí. Los sistemas se integran con quien ya atiende a tus clientes: la IA responde y "
            "agenda, y tu equipo entra en la conversación cuando ya hay una cita en firme."
        ),
    },
]


@bp.route("/")
def index():
    form = ContactForm()

    # Video de fondo opcional por tarjeta de sistema: si el archivo existe en
    # static/video/system-0N.mp4 se muestra, si no, se usa el degradado verde de siempre.
    system_videos = {}
    for numero in ("01", "02", "03"):
        ruta = os.path.join(current_app.static_folder, "video", f"system-{numero}.mp4")
        if os.path.exists(ruta):
            system_videos[numero] = url_for("static", filename=f"video/system-{numero}.mp4")

    # Imagen opcional por paso: aparece sola cuando exista el archivo.
    pasos = []
    for paso in PASOS:
        item = dict(paso)
        ruta_img = os.path.join(current_app.static_folder, "img", f"paso-{paso['n']}.jpg")
        item["imagen"] = (
            url_for("static", filename=f"img/paso-{paso['n']}.jpg")
            if os.path.exists(ruta_img)
            else None
        )
        pasos.append(item)

    return render_template(
        "index.html", form=form, system_videos=system_videos, pasos=pasos, faqs=FAQS
    )


@bp.route("/contacto", methods=["POST"])
@limiter.limit("5 per minute; 20 per day")  # frena spam/fuerza bruta sobre el formulario
def contacto():
    form = ContactForm()

    if not form.validate_on_submit():
        for campo, errores in form.errors.items():
            for error in errores:
                flash(f"{campo}: {error}", "error")
        return redirect(url_for("main.index"))

    if form.sitio_web.data:
        # Honeypot relleno => bot. Respondemos exito falso para no darle pistas.
        return redirect(url_for("main.index"))

    lead = Lead(
        nombre=form.nombre.data.strip(),
        email=form.email.data.strip().lower(),
        telefono=(form.telefono.data or "").strip() or None,
        mensaje=form.mensaje.data.strip(),
        ip=request.remote_addr,
    )
    db.session.add(lead)
    db.session.commit()

    flash("¡Gracias! Te contactaremos pronto.", "success")
    return redirect(url_for("main.index"))


@bp.route("/panel/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")  # frena intentos de fuerza bruta al login
def panel_login():
    form = LoginForm()

    if form.validate_on_submit():
        usuario_ok = form.usuario.data == current_app.config["ADMIN_USER"]
        hash_configurado = current_app.config["ADMIN_PASSWORD_HASH"]
        password_ok = bool(hash_configurado) and check_password_hash(
            hash_configurado, form.contrasena.data
        )

        if usuario_ok and password_ok:
            session.clear()
            session["admin_autenticado"] = True
            return redirect(url_for("main.panel"))

        # Mensaje generico: no revelar si fallo el usuario o la contrasena
        flash("Usuario o contraseña incorrectos.", "error")

    return render_template("panel_login.html", form=form)


@bp.route("/panel/logout")
def panel_logout():
    session.clear()
    return redirect(url_for("main.panel_login"))


@bp.route("/panel")
@login_requerido
def panel():
    leads = Lead.query.order_by(Lead.creado_en.desc()).all()
    return render_template("panel.html", leads=leads)
