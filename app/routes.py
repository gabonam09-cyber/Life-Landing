import os

import secrets

from flask import (Blueprint, current_app, flash, jsonify, redirect, render_template,
                   request, send_file, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from .config import usuarios_panel
from .exportar import construir_excel, nombre_archivo

from .analitica import (clics_para_mapa, purgar_analitica_vieja, registrar_eventos,
                        reiniciar_metricas, resumen_metricas)
from .extensions import csrf, limiter
from .forms import ContactForm, LoginForm
from .models import Lead, db
from .notificaciones import avisar_lead_nuevo
from .security import login_requerido

bp = Blueprint("main", __name__)

# Hash de una contrasena aleatoria que nadie conoce. Se usa para que un intento
# con usuario inexistente tarde lo mismo que uno con usuario real: si no, el
# tiempo de respuesta revelaria que nombres estan dados de alta.
_SENUELO = None


def _hash_senuelo():
    global _SENUELO
    if _SENUELO is None:
        _SENUELO = generate_password_hash(secrets.token_hex(16))
    return _SENUELO

# Proceso paso a paso del sistema life: primero entendemos, después ejecutamos.
PROCESO = [
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


# Preguntas frecuentes: cada una rompe una objecion concreta que frena la decision,
# no explica el servicio. Las informativas ya se responden en el resto del sitio.
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
            "Sí. Los sistemas se integran con quien ya atiende a tus clientes: la IA responde "
            "y agenda, y tu equipo entra en la conversación cuando ya hay una cita en firme."
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

    return render_template(
        "index.html",
        form=form,
        system_videos=system_videos,
        faqs=FAQS,
        proceso=PROCESO,
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
        clinica=(form.clinica.data or "").strip() or None,
        # La columna es NOT NULL en la base ya creada, asi que un campo vacio se
        # guarda como cadena vacia: evita migrar la tabla en produccion.
        email=(form.email.data or "").strip().lower(),
        telefono=(form.telefono.data or "").strip() or None,
        mensaje=(form.mensaje.data or "").strip(),
        ip=request.remote_addr,
    )
    db.session.add(lead)
    db.session.commit()

    # El aviso va DESPUES del commit y en segundo plano: si el correo falla,
    # el lead ya está a salvo en la base de datos.
    avisar_lead_nuevo(
        current_app._get_current_object(),
        {
            "nombre": lead.nombre,
            "clinica": lead.clinica,
            "email": lead.email,
            "telefono": lead.telefono,
            "mensaje": lead.mensaje,
            "creado_en": lead.creado_en.strftime("%d/%m/%Y %H:%M UTC"),
        },
    )

    flash("¡Gracias! Te contactaremos pronto.", "success")
    return redirect(url_for("main.index"))


@bp.route("/api/eventos", methods=["POST"])
@csrf.exempt  # lo llama el propio navegador con sendBeacon, que no manda formulario
@limiter.limit("60 per minute")  # limite propio: el general (50/hora) lo agotaria una visita
def api_eventos():
    """Recibe los lotes de metricas que manda analitica.js."""
    # sendBeacon puede mandar el cuerpo como text/plain, asi que no se exige
    # el Content-Type de JSON: se intenta parsear de todos modos.
    datos = request.get_json(silent=True, force=True)

    aceptado = registrar_eventos(
        datos,
        # Las visitas propias no deben contar en las metricas.
        es_interna=bool(session.get("admin_autenticado")),
        propio_host=request.host,
    )

    if not aceptado:
        return jsonify({"ok": False}), 400

    return jsonify({"ok": True}), 202


@bp.route("/panel/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")  # frena intentos de fuerza bruta al login
def panel_login():
    form = LoginForm()

    if form.validate_on_submit():
        cuentas = usuarios_panel()
        usuario = (form.usuario.data or "").strip()

        # Si el usuario no existe se comprueba igual contra un hash señuelo: sin
        # eso, un fallo instantaneo delataria que ese nombre no esta dado de alta.
        hash_guardado = cuentas.get(usuario) or _hash_senuelo()
        password_ok = check_password_hash(hash_guardado, form.contrasena.data)

        if usuario in cuentas and password_ok:
            session.clear()
            session["admin_autenticado"] = True
            session["admin_usuario"] = usuario
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


@bp.route("/panel/descargar.xlsx")
@login_requerido
def panel_descargar():
    """Todo el contenido del panel en un Excel: prospectos, visitas y clics."""
    return send_file(
        construir_excel(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=nombre_archivo(),
    )


@bp.route("/panel/metricas/reiniciar", methods=["POST"])
@login_requerido
def panel_reiniciar_metricas():
    """Deja el contador de visitas en cero. Los prospectos no se tocan."""
    solo_internas = request.form.get("alcance") == "internas"

    borrado = reiniciar_metricas(solo_internas=solo_internas)

    if not borrado["sesiones"]:
        flash("No había visitas que borrar.", "success")
    else:
        que = "tus visitas de prueba" if solo_internas else "las visitas"
        flash(f"Se borraron {que}: {borrado['sesiones']} visitas "
              f"y {borrado['clics']} clics. Los prospectos siguen intactos.", "success")

    return redirect(url_for("main.panel_metricas"))


@bp.route("/salud")
@limiter.exempt  # la pensa un vigilante externo cada pocos minutos
def salud():
    """Respuesta minima para comprobar que el servicio sigue en pie.

    En el plan gratuito el servidor se duerme sin visitas; un servicio externo
    puede llamar aqui cada pocos minutos para mantenerlo despierto. No devuelve
    HTML ni ejecuta javascript, asi que no ensucia las metricas con visitas falsas.
    """
    return {"estado": "ok"}, 200


@bp.route("/panel/metricas")
@login_requerido
def panel_metricas():
    """Que hace la gente en la landing: origen, recorrido, video y mapa de clics."""
    dias = request.args.get("dias", type=int, default=30)
    if dias not in (7, 30, 90, 0):  # 0 = todo el historico
        dias = 30

    dispositivo = request.args.get("dispositivo", default="escritorio")
    if dispositivo not in ("movil", "tablet", "escritorio"):
        dispositivo = "escritorio"

    # Ver tus propias visitas es util para probar que la medicion funciona.
    internas = request.args.get("internas") == "1"

    # Se aprovecha la visita al panel para tirar lo viejo: sin tareas programadas
    # en el plan gratuito, este es el momento natural para hacer limpieza.
    purgar_analitica_vieja(dias=90)

    return render_template(
        "panel_metricas.html",
        m=resumen_metricas(dias=dias, incluir_internas=internas),
        clics=clics_para_mapa(dias=dias, dispositivo=dispositivo, incluir_internas=internas),
        dispositivo=dispositivo,
        dias=dias,
        internas=internas,
    )
