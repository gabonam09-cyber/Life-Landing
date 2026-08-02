import os

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from .extensions import limiter
from .forms import ContactForm, LoginForm
from .models import Lead, db
from .notificaciones import avisar_lead_nuevo
from .security import login_requerido

bp = Blueprint("main", __name__)

# Creencias que frenan la decision, tomadas de las objeciones reales del
# documento de cliente ideal. Cada una es una frase que el dueño ya se dijo.
CREENCIAS = [
    {
        "creencia": "\"Mis pacientes quieren trato humano, no un robot.\"",
        "respuesta": (
            "Y lo van a seguir teniendo. La IA responde lo que se pregunta cien veces al día: "
            "horarios, ubicación, precios, disponibilidad. En cuanto alguien pregunta por un "
            "tratamiento concreto, la conversación pasa a tu equipo. Nadie recibe un diagnóstico "
            "de un bot."
        ),
    },
    {
        "creencia": "\"Ya contraté una agencia y solo tiré el dinero.\"",
        "respuesta": (
            "Nos lo dicen en casi todas las llamadas. Por eso no vendemos alcance ni "
            "seguidores: lo que medimos cada semana es cuántos escribieron, cuántos agendaron "
            "y cuántos se presentaron. Si eso no sube, no hay nada que presumir."
        ),
    },
    {
        "creencia": "\"Yo no sé de tecnología, esto me va a complicar más.\"",
        "respuesta": (
            "Tú no configuras nada. Lo montamos nosotros sobre el WhatsApp que ya usas, y tu "
            "recepción sigue trabajando igual. Lo único que cambia es que deja de contestar lo "
            "mismo todo el día."
        ),
    },
    {
        "creencia": "\"Si ya no me doy abasto, ¿para qué quiero más pacientes?\"",
        "respuesta": (
            "Porque el problema no suele ser el volumen, es el desorden: huecos a media mañana, "
            "saturación el sábado y ausentes que tiran el espacio. El sistema ordena la agenda "
            "antes de llenarla."
        ),
    },
    {
        "creencia": "\"Automatizar va a abaratar la imagen de mi clínica.\"",
        "respuesta": (
            "Lo que abarata la imagen es tardar seis horas en contestar un mensaje. Responder "
            "en segundos, con tu tono y tu información, se lee como una clínica que tiene su "
            "operación en orden."
        ),
    },
]


# Como se ve la clinica una vez funcionando el sistema. Escrito con los deseos
# del documento: agenda llena, no-shows, pacientes calificados, tiempo libre.
RESULTADOS = [
    {
        "titulo": "Abres con la agenda llena",
        "texto": "Las citas que se agendaron de madrugada ya están ahí cuando llegas a la clínica.",
    },
    {
        "titulo": "Bajan los pacientes que no llegan",
        "texto": "Recordatorios automáticos antes de cada cita, para que el espacio no se tire.",
    },
    {
        "titulo": "Llegan pacientes, no preguntones",
        "texto": "Las campañas filtran a quien solo busca precio y dejan pasar a quien sí va a tratarse.",
    },
    {
        "titulo": "Nadie espera respuesta",
        "texto": "Cada mensaje se contesta al momento, a las 11 de la noche y en domingo.",
    },
    {
        "titulo": "Vuelven los que ya cotizaron",
        "texto": "El sistema reactiva solo a los pacientes que preguntaron hace meses y nunca volvieron.",
    },
    {
        "titulo": "Ves los números desde el celular",
        "texto": "Cuántos escribieron, cuántos agendaron, cuántos asistieron y cuánto se vendió.",
    },
]


# Que incluye el sistema. Es la oferta ya definida en el documento de datos base:
# el visitante debe saber que se le va a proponer antes de entrar al Zoom.
INCLUYE = [
    "Auditoría de tu embudo actual de pacientes",
    "Campañas de anuncios que filtran curiosos, no pacientes reales",
    "Bot de WhatsApp con IA que agenda citas 24/7",
    "Recordatorios automáticos que reducen tus ausencias",
    "Reactivación de pacientes que cotizaron y nunca volvieron",
    "Seguimiento post-tratamiento para que regresen",
    "Panel de control: tus citas y ventas desde el celular",
]


# Preguntas frecuentes: cada una rompe una objecion concreta que frena la decision,
# no explica el servicio. Las informativas ya se responden en el resto del sitio.
FAQS = [
    {
        "n": "01",
        "pregunta": "¿Qué pasa exactamente en esa reunión?",
        "respuesta": (
            "Son unos 30 minutos por Zoom o Meet. Revisamos contigo cómo llegan hoy tus "
            "pacientes, por dónde se están cayendo y qué sistema haría falta. Sales de ahí con "
            "la propuesta explicada. No se firma nada en esa llamada ni te vamos a presionar "
            "para decidir en caliente: lo revisas con calma y, si tiene sentido, hablamos otra vez."
        ),
    },
    {
        "n": "02",
        "pregunta": "¿Tiene costo la reunión?",
        "respuesta": (
            "No. La reunión y la revisión previa de tu clínica no cuestan nada y no te "
            "comprometen a nada. Si al revisarla no vemos una oportunidad clara, te lo decimos "
            "y ahí queda: preferimos eso a venderte algo que no te va a mover los números."
        ),
    },
    {
        "n": "03",
        "pregunta": "Ya trabajé con una agencia y no funcionó. ¿Por qué ustedes sí?",
        "respuesta": (
            "Es lo que más escuchamos. La diferencia es qué medimos: no te vamos a enseñar "
            "alcance ni seguidores, sino cuántos pacientes escribieron, cuántos agendaron y "
            "cuántos se presentaron. Esos tres números se revisan cada semana contigo, así que "
            "si algo no está sirviendo se ve en semanas, no en seis meses."
        ),
    },
    {
        "n": "04",
        "pregunta": "Mis pacientes son mayores y no usan tanto WhatsApp. ¿Igual sirve?",
        "respuesta": (
            "En ese caso el peso no está en el bot, sino en que aparezcas en Google cuando "
            "buscan tu especialidad en la zona, en cuidar tus reseñas y en los recordatorios "
            "de cita. Eso lo vemos en la reunión: si tu paciente no está en WhatsApp, no tiene "
            "sentido cobrarte por un bot de WhatsApp."
        ),
    },
    {
        "n": "05",
        "pregunta": "¿Cuánto cuesta y me amarran a un contrato?",
        "respuesta": (
            "El precio depende de qué necesite tu clínica: no cuesta lo mismo ordenar solo la "
            "respuesta por WhatsApp que montar captación, respuesta y reputación juntas. El "
            "número sale en la reunión y te lo mandamos por escrito. No trabajamos con "
            "permanencias forzadas: la idea es que sigas porque los números te lo justifican."
        ),
    },
    {
        "n": "06",
        "pregunta": "Tengo que consultarlo con mi socio o el director médico.",
        "respuesta": (
            "Perfecto, tráelo a la reunión. Y si no puede, te mandamos la propuesta por escrito "
            "para que se la enseñes: precio, alcance y plazos, sin letra chica. Es justo por eso "
            "que en la primera llamada no se cierra nada."
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
        creencias=CREENCIAS,
        resultados=RESULTADOS,
        incluye=INCLUYE,
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
        clinica=form.clinica.data.strip(),
        email=form.email.data.strip().lower(),
        telefono=(form.telefono.data or "").strip() or None,
        mensaje=form.mensaje.data.strip(),
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
