from functools import wraps

from flask import redirect, session, url_for


def registrar_headers_seguridad(app):
    """Agrega cabeceras HTTP de seguridad a toda respuesta del sitio."""

    @app.after_request
    def _headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # HSTS: fuerza HTTPS en el navegador una vez visitado por primera vez
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # CSP: solo permite recursos propios + Google Fonts (usados por la identidad de marca)
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "script-src 'self'; "
            "frame-ancestors 'none'"
        )
        return resp


def login_requerido(vista):
    """Protege rutas del panel: sin sesion activa, redirige al login."""

    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not session.get("admin_autenticado"):
            return redirect(url_for("main.panel_login"))
        return vista(*args, **kwargs)

    return envoltura
