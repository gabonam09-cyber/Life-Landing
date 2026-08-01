from flask_wtf import FlaskForm
from wtforms import HiddenField, PasswordField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class ContactForm(FlaskForm):
    """Flask-WTF agrega proteccion CSRF automatica a este formulario."""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=120)])
    # El objetivo del formulario es agendar un Zoom: sin saber de que clinica se
    # trata no se puede preparar la reunion ni revisar su presencia digital antes.
    clinica = StringField("Clínica o spa", validators=[DataRequired(), Length(min=2, max=140)])
    email = StringField("Correo", validators=[DataRequired(), Email(), Length(max=120)])
    telefono = StringField("WhatsApp", validators=[DataRequired(), Length(min=8, max=30)])
    mensaje = TextAreaField("Mensaje", validators=[DataRequired(), Length(min=10, max=2000)])

    # Honeypot: invisible para humanos (oculto por CSS), los bots de spam
    # suelen rellenar todos los campos que encuentran. Si esto llega con
    # contenido, es un bot y se descarta silenciosamente.
    sitio_web = HiddenField()


class LoginForm(FlaskForm):
    usuario = StringField("Usuario", validators=[DataRequired(), Length(max=80)])
    contrasena = PasswordField("Contraseña", validators=[DataRequired(), Length(max=200)])
