import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import get_config
from .extensions import csrf, limiter
from .models import db
from .security import registrar_headers_seguridad


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(get_config())

    if not app.config["SECRET_KEY"]:
        raise RuntimeError(
            "Falta SECRET_KEY en el entorno (.env). Genera una con: "
            "python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # Detras del proxy de Render, request.remote_addr seria la IP del proxy y no
    # la del visitante: el limitador veria todo el trafico como una sola persona
    # y acabaria bloqueando a todo el mundo. Ademas el lead guardaria una IP inutil.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # En algunos hosts el disco es de solo lectura; la carpeta instance/ solo
    # hace falta para el SQLite de desarrollo, asi que no debe tumbar el arranque.
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    registrar_headers_seguridad(app)

    from .routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()

    return app
