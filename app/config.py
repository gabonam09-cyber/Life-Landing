import os


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

    ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
    ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")

    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

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
