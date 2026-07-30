from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Lead(db.Model):
    """Un prospecto que llego por el formulario de contacto del sitio."""

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30), nullable=True)
    mensaje = db.Column(db.Text, nullable=False)
    ip = db.Column(db.String(45), nullable=True)  # soporta IPv6
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Lead {self.nombre} ({self.email})>"
