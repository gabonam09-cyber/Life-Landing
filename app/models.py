from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Lead(db.Model):
    """Un prospecto que llego por el formulario de contacto del sitio."""

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    clinica = db.Column(db.String(140), nullable=True)
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30), nullable=True)
    mensaje = db.Column(db.Text, nullable=False)
    ip = db.Column(db.String(45), nullable=True)  # soporta IPv6
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Lead {self.nombre} ({self.email})>"


class Sesion(db.Model):
    """Una visita anonima a la landing.

    No se guarda la IP ni nada que identifique a la persona: el token es un
    identificador aleatorio que vive en una cookie propia y solo sirve para
    juntar los eventos de una misma visita.
    """

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(36), unique=True, nullable=False, index=True)

    creada_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    ultima_actividad = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # De donde llego: whatsapp, instagram, google, directo u otro.
    origen = db.Column(db.String(20), nullable=False, default="directo", index=True)
    referrer = db.Column(db.String(300), nullable=True)

    dispositivo = db.Column(db.String(12), nullable=False, default="escritorio", index=True)
    ancho = db.Column(db.Integer, nullable=True)
    alto = db.Column(db.Integer, nullable=True)

    duracion_seg = db.Column(db.Integer, nullable=False, default=0)
    scroll_max_pct = db.Column(db.Integer, nullable=False, default=0)

    # Las visitas propias (con sesion de admin abierta) no deben ensuciar los numeros.
    es_interna = db.Column(db.Boolean, nullable=False, default=False, index=True)

    secciones = db.relationship("SeccionVista", backref="sesion", cascade="all, delete-orphan")
    clics = db.relationship("Clic", backref="sesion", cascade="all, delete-orphan")
    video = db.relationship("VideoVista", backref="sesion", uselist=False,
                            cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Sesion {self.token[:8]} {self.origen} {self.dispositivo}>"


class SeccionVista(db.Model):
    """Cuanto tiempo tuvo en pantalla una seccion concreta durante una visita."""

    id = db.Column(db.Integer, primary_key=True)
    sesion_id = db.Column(db.Integer, db.ForeignKey("sesion.id"), nullable=False, index=True)

    seccion = db.Column(db.String(40), nullable=False, index=True)
    segundos = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (db.UniqueConstraint("sesion_id", "seccion", name="uq_seccion_por_sesion"),)


class VideoVista(db.Model):
    """Como se comporto una visita con el video del hero. Una fila por sesion."""

    id = db.Column(db.Integer, primary_key=True)
    sesion_id = db.Column(db.Integer, db.ForeignKey("sesion.id"),
                          unique=True, nullable=False, index=True)

    dio_play = db.Column(db.Boolean, nullable=False, default=False)
    segundos_vistos = db.Column(db.Integer, nullable=False, default=0)
    pct_completado = db.Column(db.Integer, nullable=False, default=0)
    # Segundo del video en el que dejo de verlo: es lo que dibuja la curva de abandono.
    abandono_seg = db.Column(db.Integer, nullable=True)
    duracion_seg = db.Column(db.Integer, nullable=True)


class Clic(db.Model):
    """Un clic, en coordenadas comparables entre pantallas distintas.

    La X se guarda como fraccion (0-1) del ancho del contenido y la Y en pixeles
    desde el inicio del documento. Asi el mapa se puede repintar a cualquier
    ancho, siempre que se comparen visitas del mismo tipo de dispositivo.
    """

    id = db.Column(db.Integer, primary_key=True)
    sesion_id = db.Column(db.Integer, db.ForeignKey("sesion.id"), nullable=False, index=True)

    x_rel = db.Column(db.Float, nullable=False)
    y_abs = db.Column(db.Integer, nullable=False)
    ancho_ref = db.Column(db.Integer, nullable=False)
    dispositivo = db.Column(db.String(12), nullable=False, index=True)

    elemento = db.Column(db.String(120), nullable=True)
    texto = db.Column(db.String(80), nullable=True)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
