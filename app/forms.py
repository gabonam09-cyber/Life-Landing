from flask_wtf import FlaskForm
from wtforms import HiddenField, PasswordField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class ContactForm(FlaskForm):
    """Flask-WTF agrega proteccion CSRF automatica a este formulario."""

    nombre = StringField("Nombre completo", validators=[DataRequired(), Length(min=2, max=120)])
    # El campo ya no se muestra en el formulario, pero se conserva por si algun
    # lead viejo del panel lo trae guardado.
    clinica = StringField("Negocio", validators=[Optional(), Length(max=140)])
    # Correo y mensaje son opcionales: el formulario no debe frenar a nadie por
    # un campo de mas. Si escriben correo, igual tiene que ser uno valido.
    email = StringField("Correo", validators=[Optional(), Email(), Length(max=120)])
    telefono = StringField("Teléfono", validators=[Optional(), Length(min=8, max=30)])
    mensaje = TextAreaField("¿Qué necesita tu negocio?", validators=[Optional(), Length(max=2000)])

    # Honeypot: invisible para humanos (oculto por CSS), los bots de spam
    # suelen rellenar todos los campos que encuentran. Si esto llega con
    # contenido, es un bot y se descarta silenciosamente.
    sitio_web = HiddenField()


class LoginForm(FlaskForm):
    usuario = StringField("Usuario", validators=[DataRequired(), Length(max=80)])
    contrasena = PasswordField("Contraseña", validators=[DataRequired(), Length(max=200)])
