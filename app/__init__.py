import os

from flask import Flask

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

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    registrar_headers_seguridad(app)

    from .routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()

    return app
