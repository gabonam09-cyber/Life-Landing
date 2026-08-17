import os


def usuarios_panel():
    """Cuentas que pueden entrar al panel, como {usuario: hash de contrasena}.

    Cada socio tiene la suya: ADMIN_USER / ADMIN_PASSWORD_HASH para la primera y
    ADMIN_USER_2 / ADMIN_PASSWORD_HASH_2 (o _3, _4...) para las siguientes. Se
    leen del entorno en cada consulta para no tener que reiniciar al agregar una.
    """
    cuentas = {}

    for sufijo in [""] + [f"_{n}" for n in range(2, 11)]:
        usuario = os.environ.get(f"ADMIN_USER{sufijo}", "").strip()
        hash_clave = os.environ.get(f"ADMIN_PASSWORD_HASH{sufijo}", "").strip()
        if usuario and hash_clave:
            cuentas[usuario] = hash_clave

    return cuentas


def _normalizar_url_bd(url):
    """Adapta la URL de Postgres que entregan los hosts al formato de SQLAlchemy 2.

    Render (como Heroku) publica DATABASE_URL con el esquema `postgres://`, que
    SQLAlchemy 2 ya no reconoce. Ademas, sin driver explicito intentaria usar
    psycopg2, que no esta instalado: aqui se usa psycopg 3.
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Config:
    # Nunca hardcodear secretos: todo viene de variables de entorno (.env)
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # En local, ruta relativa: Flask-SQLAlchemy la resuelve contra
    # app.instance_path (la carpeta instance/). En produccion llega un Postgres.
    SQLALCHEMY_DATABASE_URI = _normalizar_url_bd(
        os.environ.get("DATABASE_URL", "sqlite:///life.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Acceso al panel. Cada socio tiene su propio usuario y su propia
    # contrasena: ADMIN_USER / ADMIN_PASSWORD_HASH para el primero, y despues
    # ADMIN_USER_2 / ADMIN_PASSWORD_HASH_2, _3, etc. Asi se agregan mas sin
    # tocar codigo, solo variables de entorno.
    ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
    ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")

    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    # Aviso por correo al entrar un lead. Si faltan credenciales, el sitio
    # funciona igual: simplemente no manda el aviso.
    #
    # Via preferida: API HTTP (puerto 443). Es la unica que funciona en el plan
    # gratuito de Render, que bloquea los puertos SMTP.
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
    REMITENTE_API = os.environ.get("REMITENTE_API", "life <onboarding@resend.dev>")

    # Via alternativa: SMTP. Solo en local o con un plan de pago en Render.
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
    NOTIFICAR_A = os.environ.get("NOTIFICAR_A") or os.environ.get("SMTP_USER")
    URL_PANEL = os.environ.get("URL_PANEL", "/panel")

    # Cookies de sesion: solo viajan por HTTPS en produccion, nunca accesibles por JS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("FORCE_HTTPS", "true").lower() == "true"

    WTF_CSRF_TIME_LIMIT = None  # el token CSRF no expira por tiempo en formularios largos


class DevConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # en localhost no hay HTTPS


class ProdConfig(Config):
    DEBUG = False


def get_config():
    env = os.environ.get("FLASK_ENV", "production").lower()
    return DevConfig if env == "development" else ProdConfig
